#!/usr/bin/env python3
"""
Upload ONNX models to S3 staging bucket.

Usage:
    python scripts/upload_model.py <model_file> --name <s3_name> [--force]

Examples:
    python scripts/upload_model.py annotator.onnx --name annotator.onnx
    python scripts/upload_model.py my_model.onnx --name cpu_specialist.onnx --force
"""
import argparse
import boto3
import os
import sys
from pathlib import Path


STAGING_BUCKET = "aero-sentry-2026-staging-artifacts"
MODELS_PREFIX = "models/"


def upload_model(file_path: str, s3_name: str, force: bool = False) -> bool:
    """
    Upload a model to S3 staging bucket.
    
    Args:
        file_path: Local path to the model file
        s3_name: Name to use in S3 (will be prefixed with 'models/')
        force: If True, overwrite existing model
        
    Returns:
        True if upload successful, False otherwise
    """
    # Validate file exists
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return False
    
    # Initialize S3 client
    s3_client = boto3.client('s3', region_name='us-east-1')
    s3_key = f"{MODELS_PREFIX}{s3_name}"
    
    # Check if model already exists
    try:
        s3_client.head_object(Bucket=STAGING_BUCKET, Key=s3_key)
        if not force:
            print(f"ERROR: Model already exists at s3://{STAGING_BUCKET}/{s3_key}")
            print("Use --force to overwrite")
            return False
        else:
            print(f"WARNING: Overwriting existing model at s3://{STAGING_BUCKET}/{s3_key}")
    except s3_client.exceptions.ClientError as e:
        # 404 means object doesn't exist, which is fine
        if e.response['Error']['Code'] != '404':
            print(f"ERROR: Failed to check model existence: {e}")
            return False
    
    # Upload model
    try:
        file_size = os.path.getsize(file_path)
        print(f"Uploading {file_path} ({file_size / 1024 / 1024:.2f} MB) to s3://{STAGING_BUCKET}/{s3_key}")
        
        # Upload with progress callback
        def progress_callback(bytes_transferred):
            percent = (bytes_transferred / file_size) * 100
            print(f"\rProgress: {percent:.1f}%", end='', flush=True)
        
        s3_client.upload_file(
            file_path,
            STAGING_BUCKET,
            s3_key,
            Callback=progress_callback
        )
        print("\n✓ Upload successful!")
        
        # Verify upload
        response = s3_client.head_object(Bucket=STAGING_BUCKET, Key=s3_key)
        uploaded_size = response['ContentLength']
        if uploaded_size == file_size:
            print(f"✓ Verified: {uploaded_size / 1024 / 1024:.2f} MB")
            return True
        else:
            print(f"WARNING: Size mismatch - local: {file_size}, S3: {uploaded_size}")
            return False
            
    except Exception as e:
        print(f"\nERROR: Upload failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Upload ONNX models to S3 staging bucket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/upload_model.py annotator.onnx --name annotator.onnx
  python scripts/upload_model.py my_model.onnx --name cpu_specialist.onnx --force
        """
    )
    
    parser.add_argument(
        'file',
        type=str,
        help='Path to the model file to upload'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Name to use for the model in S3 (e.g., annotator.onnx)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite model if it already exists'
    )
    
    args = parser.parse_args()
    
    # Upload model
    success = upload_model(args.file, args.name, args.force)
    
    if success:
        print(f"\nModel available at: s3://{STAGING_BUCKET}/{MODELS_PREFIX}{args.name}")
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
