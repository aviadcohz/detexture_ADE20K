#!/usr/bin/env python3
"""Prepare assets for the Architexture GitHub Pages site.

Reads dataset metadata, copies/compresses images, and generates gallery.json.
"""

import json
import shutil
from pathlib import Path
from PIL import Image
import sys

# Paths
DATASET = Path("/datasets/ade20k/Detecture_dataset_x2")
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


def compress_refined(src_path: Path, dst_path: Path):
    """Convert refined PNG to JPEG q85."""
    try:
        img = Image.open(src_path).convert("RGB")
        img.save(dst_path, "JPEG", quality=85)
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

    # Build source image index (deduplicate by source_image_id)
    # Map source_image_id -> source image path from transitions
    source_images = {}
    for t in transitions:
        img_path = t["image"]
        # Extract source_image_id from transition filename
        # e.g. "training_ADE_train_00000191_t0" -> "training_ADE_train_00000191"
        fname = Path(img_path).stem
        # Remove _t{N} suffix to get source_image_id
        parts = fname.rsplit("_t", 1)
        source_id = parts[0] if len(parts) == 2 else fname
        if source_id not in source_images:
            source_images[source_id] = img_path

    print(f"  {len(source_images)} unique source images")

    # Step 1: Copy source image thumbnails
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

    # Step 2: Copy crop images (as-is, already small)
    print("\nCopying crop images...")
    crops_dir = ASSETS / "crops"
    crops_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        src = Path(crop["image_path"])
        dst = crops_dir / src.name
        if not dst.exists():
            shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} crops")

    # Step 3: Copy crop masks (as-is)
    print("\nCopying crop masks...")
    masks_dir = ASSETS / "masks"
    masks_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        for key in ("mask_a_path", "mask_b_path"):
            src = Path(crop[key])
            dst = masks_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops) * 2} masks")

    # Step 4: Compress refined crops (PNG -> JPEG)
    print("\nCompressing refined crops...")
    refined_dir = ASSETS / "refined"
    refined_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        src = Path(crop["refined_image_path"])
        dst = refined_dir / (src.stem + ".jpg")
        if not dst.exists():
            compress_refined(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} refined crops")

    # Step 5: Copy refined masks (as-is)
    print("\nCopying refined masks...")
    refined_masks_dir = ASSETS / "refined_masks"
    refined_masks_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        for key in ("refined_mask_a_path", "refined_mask_b_path"):
            src = Path(crop[key])
            dst = refined_masks_dir / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops) * 2} refined masks")

    # Step 6: Copy overlays (per transition, deduplicated)
    print("\nCopying overlays...")
    overlays_dir = ASSETS / "overlays"
    overlays_dir.mkdir(parents=True, exist_ok=True)
    overlay_sizes = {}  # transition_name -> (w, h)
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
                overlay_sizes[trans] = img.size  # (w, h)
    print(f"  Done: {len(seen_transitions)} overlays")

    # Step 7: Copy crop visualizations
    print("\nCopying crop visualizations...")
    crop_viz_dir = ASSETS / "crop_viz"
    crop_viz_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        crop_name = crop["crop_name"]
        src = DATASET / "crops" / "visualizations" / f"{crop_name}.jpg"
        dst = crop_viz_dir / f"{crop_name}.jpg"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} crop visualizations")

    # Step 8: Copy refined crop visualizations
    print("\nCopying refined crop visualizations...")
    refined_viz_dir = ASSETS / "refined_viz"
    refined_viz_dir.mkdir(parents=True, exist_ok=True)
    for i, crop in enumerate(crops):
        crop_name = crop["crop_name"]
        src = DATASET / "crops" / "refined" / "visualizations" / f"{crop_name}.jpg"
        dst = refined_viz_dir / f"{crop_name}.jpg"
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
        if (i + 1) % 200 == 0:
            print(f"  {i + 1}/{len(crops)}")
    print(f"  Done: {len(crops)} refined crop visualizations")

    # Step 9: Copy transition-level source images (the actual photos)
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
        crop_name = crop["crop_name"]
        source_id = crop.get("source_image_id", "")
        coords = crop.get("coords", [])
        w = coords[3] - coords[1] if len(coords) == 4 else 0
        h = coords[2] - coords[0] if len(coords) == 4 else 0
        refined_size = crop.get("refined_size", [0, 0])

        source_transition = crop.get("source_transition", "")
        source_box = crop.get("source_box", [0, 0, 0, 0])
        ov_size = overlay_sizes.get(source_transition, (256, 256))

        entry = {
            "crop_name": crop_name,
            "source_image_id": source_id,
            "source_transition": source_transition,
            "texture_a": crop.get("texture_a", ""),
            "texture_b": crop.get("texture_b", ""),
            "crop_width": w,
            "crop_height": h,
            "refined_width": refined_size[1] if len(refined_size) > 1 else 0,
            "refined_height": refined_size[0] if len(refined_size) > 0 else 0,
            "scale_factor": crop.get("scale_factor", 1),
            "balance": crop.get("balance", [0, 0]),
            "crop_score": crop.get("crop_score", 0),
            "source_box": source_box,
            "overlay_w": ov_size[0],
            "overlay_h": ov_size[1],
            # Relative paths for the site
            "source_thumb": f"assets/sources/{source_id}.jpg",
            "crop_image": f"assets/crops/{Path(crop['image_path']).name}",
            "mask_a": f"assets/masks/{Path(crop['mask_a_path']).name}",
            "mask_b": f"assets/masks/{Path(crop['mask_b_path']).name}",
            "refined_image": f"assets/refined/{Path(crop['refined_image_path']).stem}.jpg",
            "refined_mask_a": f"assets/refined_masks/{Path(crop['refined_mask_a_path']).name}",
            "refined_mask_b": f"assets/refined_masks/{Path(crop['refined_mask_b_path']).name}",
            "overlay": f"assets/overlays/{source_transition}.jpg",
            "crop_viz": f"assets/crop_viz/{crop_name}.jpg",
            "refined_viz": f"assets/refined_viz/{crop_name}.jpg",
            "trans_image": f"assets/trans_images/{source_transition}.jpg",
        }
        gallery_entries.append(entry)

    gallery = {
        "stats": {
            "total_input_images": stats.get("total_images", 525),
            "images_processed": stats.get("processed", 455),
            "failed": stats.get("failed", 70),
            "transitions_found": stats.get("transitions_found", 734),
            "total_crops": stats.get("total_crops", 1057),
            "refined_count": stats.get("refined_count", 1057),
            "mean_crop_input_px": stats.get("crop_input_min_side_mean", 103),
            "mean_refined_output_px": stats.get("refined_output_min_side_mean", 206),
            "processing_time_sec": stats.get("elapsed_seconds", 1764.6),
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
