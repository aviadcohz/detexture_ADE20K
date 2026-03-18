#!/usr/bin/env python3
"""Prepare assets for the DeTexture GitHub Pages site.

Reads the unified pipeline output (final/ = best version per crop),
copies/compresses images, and generates gallery.json.
"""

import json
import shutil
from pathlib import Path
from PIL import Image

# Paths
DATASET = Path("/datasets/ade20k/DeTexture")
SITE = Path(__file__).parent
ASSETS = SITE / "assets"

CROP_META = DATASET / "crops" / "metadata.json"
TRANSITION_META = DATASET / "metadata.json"
STATS_FILE = DATASET / "stats.json"


def thumbnail_source(src_path: Path, dst_path: Path, max_side=256):
    """Resize source image to thumbnail, JPEG q80."""
    try:
        img = Image.open(src_path)
        img.thumbnail((max_side, max_side), Image.LANCZOS)
        img = img.convert("RGB")
        img.save(dst_path, "JPEG", quality=80)
    except Exception as e:
        print(f"  WARN: Failed to thumbnail {src_path}: {e}")


def compress_to_jpeg(src_path: Path, dst_path: Path, quality=85):
    """Convert any image to JPEG."""
    try:
        img = Image.open(src_path).convert("RGB")
        img.save(dst_path, "JPEG", quality=quality)
    except Exception as e:
        print(f"  WARN: Failed to compress {src_path}: {e}")


def main():
    print("Loading metadata...")
    with open(CROP_META) as f:
        crops = json.load(f)
    with open(TRANSITION_META) as f:
        transitions = json.load(f)
    with open(STATS_FILE) as f:
        stats = json.load(f)

    print(f"  {len(crops)} crops, {len(transitions)} transitions")

    # Build source image index
    source_images = {}
    for t in transitions:
        img_path = t.get("image", "")
        if not img_path:
            continue
        fname = Path(img_path).stem
        parts = fname.rsplit("_t", 1)
        source_id = parts[0] if len(parts) == 2 else fname
        if source_id not in source_images:
            source_images[source_id] = img_path
    print(f"  {len(source_images)} unique source images")

    # Step 1: Source thumbnails
    print("\nCopying source thumbnails...")
    sources_dir = ASSETS / "sources"
    sources_dir.mkdir(parents=True, exist_ok=True)
    for i, (src_id, src_path) in enumerate(sorted(source_images.items())):
        dst = sources_dir / f"{src_id}.jpg"
        if not dst.exists():
            thumbnail_source(Path(src_path), dst)
        if (i + 1) % 100 == 0:
            print(f"  {i + 1}/{len(source_images)}")
    print(f"  Done: {len(source_images)} thumbnails")

    # Step 2: Raw crop images
    print("\nCopying crop images...")
    crops_dir = ASSETS / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        src = Path(crop["image_path"])
        # image_path points to final/ — raw crops are in crops/images/
        raw_src = DATASET / "crops" / "images" / f"{crop['crop_name']}.jpg"
        dst = crops_dir / f"{crop['crop_name']}.jpg"
        if not dst.exists():
            if raw_src.exists():
                shutil.copy2(raw_src, dst)
            elif src.exists():
                shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} crops")

    # Step 3: Raw crop masks
    print("\nCopying crop masks...")
    masks_dir = ASSETS / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        name = crop["crop_name"]
        for suffix in ("mask_a", "mask_b"):
            raw_src = DATASET / "crops" / "masks_texture" / f"{name}_{suffix}.png"
            dst = masks_dir / f"{name}_{suffix}.png"
            if not dst.exists() and raw_src.exists():
                shutil.copy2(raw_src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops) * 2} masks")

    # Step 4: Final (best) images -> "refined" directory for site compat
    print("\nCopying final (best) images as refined...")
    refined_dir = ASSETS / "refined"
    refined_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        src = Path(crop["image_path"])  # points to final/
        dst = refined_dir / f"{crop['crop_name']}.jpg"
        if not dst.exists() and src.exists():
            compress_to_jpeg(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} refined crops")

    # Step 5: Final (best) masks -> "refined_masks" for site compat
    print("\nCopying final masks as refined masks...")
    refined_masks_dir = ASSETS / "refined_masks"
    refined_masks_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        name = crop["crop_name"]
        for key, suffix in [("mask_a_path", "mask_a"), ("mask_b_path", "mask_b")]:
            src = Path(crop[key])  # points to final/
            dst = refined_masks_dir / f"{name}_{suffix}.png"
            if not dst.exists() and src.exists():
                shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops) * 2} refined masks")

    # Step 6: Overlays
    print("\nCopying overlays...")
    overlays_dir = ASSETS / "overlays"
    overlays_dir.mkdir(parents=True, exist_ok=True)
    overlay_sizes = {}
    seen_transitions = set()
    for crop in crops:
        trans = crop.get("source_transition", "")
        if trans and trans not in seen_transitions:
            seen_transitions.add(trans)
            src = DATASET / "overlays" / f"{trans}.jpg"
            dst = overlays_dir / f"{trans}.jpg"
            if src.exists() and not dst.exists():
                shutil.copy2(src, dst)
            if src.exists():
                img = Image.open(src)
                overlay_sizes[trans] = img.size
    print(f"  Done: {len(seen_transitions)} overlays")

    # Step 7: Crop visualizations
    print("\nCopying crop visualizations...")
    crop_viz_dir = ASSETS / "crop_viz"
    crop_viz_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        name = crop["crop_name"]
        src = DATASET / "crops" / "visualizations" / f"{name}.jpg"
        dst = crop_viz_dir / f"{name}.jpg"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} crop visualizations")

    # Step 8: Final visualizations -> "refined_viz" for site compat
    print("\nCopying final visualizations as refined viz...")
    refined_viz_dir = ASSETS / "refined_viz"
    refined_viz_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        name = crop["crop_name"]
        src = DATASET / "final" / "visualizations" / f"{name}.jpg"
        dst = refined_viz_dir / f"{name}.jpg"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} refined visualizations")

    # Step 9: Transition source images
    print("\nCopying transition source images...")
    trans_images_dir = ASSETS / "trans_images"
    trans_images_dir.mkdir(parents=True, exist_ok=True)
    for trans in seen_transitions:
        src = DATASET / "images" / f"{trans}.jpg"
        dst = trans_images_dir / f"{trans}.jpg"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
    print(f"  Done: {len(seen_transitions)} transition images")

    # Generate gallery.json
    print("\nGenerating gallery.json...")
    gallery_entries = []
    for crop in crops:
        name = crop["crop_name"]
        source_id = crop.get("source_image_id", "")
        coords = crop.get("coords", [0, 0, 0, 0])
        crop_w = coords[2] if len(coords) > 2 else 0
        crop_h = coords[3] if len(coords) > 3 else 0

        source_transition = crop.get("source_transition", "")
        ov_size = overlay_sizes.get(source_transition, (256, 256))

        # For refined dimensions: if refined, use coords (which are final size)
        # otherwise same as crop size
        is_refined = crop.get("is_refined", False)
        scale = crop.get("scale_factor", 1)
        if is_refined:
            refined_w = crop_w
            refined_h = crop_h
            # Original raw crop size is crop_size / scale
            raw_w = crop_w // scale if scale > 0 else crop_w
            raw_h = crop_h // scale if scale > 0 else crop_h
        else:
            raw_w = crop_w
            raw_h = crop_h
            refined_w = crop_w
            refined_h = crop_h

        gallery_entries.append({
            "crop_name": name,
            "source_image_id": source_id,
            "source_transition": source_transition,
            "texture_a": crop.get("texture_a", ""),
            "texture_b": crop.get("texture_b", ""),
            "crop_width": raw_w,
            "crop_height": raw_h,
            "refined_width": refined_w,
            "refined_height": refined_h,
            "scale_factor": scale,
            "balance": crop.get("balance", [0, 0]),
            "crop_score": crop.get("crop_score", 0),
            "source_box": crop.get("source_box", [0, 0, 0, 0]),
            "overlay_w": ov_size[0],
            "overlay_h": ov_size[1],
            "source_thumb": f"assets/sources/{source_id}.jpg",
            "crop_image": f"assets/crops/{name}.jpg",
            "mask_a": f"assets/masks/{name}_mask_a.png",
            "mask_b": f"assets/masks/{name}_mask_b.png",
            "refined_image": f"assets/refined/{name}.jpg",
            "refined_mask_a": f"assets/refined_masks/{name}_mask_a.png",
            "refined_mask_b": f"assets/refined_masks/{name}_mask_b.png",
            "overlay": f"assets/overlays/{source_transition}.jpg",
            "crop_viz": f"assets/crop_viz/{name}.jpg",
            "trans_image": f"assets/trans_images/{source_transition}.jpg",
            "refined_viz": f"assets/refined_viz/{name}.jpg",
        })

    gallery = {
        "stats": {
            "total_input_images": stats.get("total_images", 0),
            "images_processed": stats.get("processed", 0),
            "failed": stats.get("failed", 0),
            "transitions_found": stats.get("transitions_found", 0),
            "total_crops": len(gallery_entries),
            "refined_count": sum(1 for c in crops if c.get("is_refined")),
            "mean_crop_input_px": stats.get("crop_input_min_side_mean", 0),
            "mean_refined_output_px": stats.get("crop_input_min_side_median", 0),
            "processing_time_sec": stats.get("elapsed_seconds", 0),
            "unique_source_images": len(source_images),
        },
        "entries": gallery_entries,
    }

    gallery_path = SITE / "gallery.json"
    with open(gallery_path, "w") as f:
        json.dump(gallery, f, indent=1)

    print(f"  Written {gallery_path} ({len(gallery_entries)} entries)")
    print("\nDone! Run 'du -sh assets/' to check total size.")


if __name__ == "__main__":
    main()
