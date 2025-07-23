#!/bin/bash

# Build the Docker image with the exact command structure required
echo "Building PDF Outline Extractor Docker image..."
docker build --platform linux/amd64 -t pdf-outline-extractor:v1.0 .

if [ $? -eq 0 ]; then
    echo "✅ Docker image built successfully!"
    echo ""
    echo "Image: pdf-outline-extractor:v1.0"
    echo "Platform: linux/amd64"
    echo ""
    echo "To run with your PDFs:"
    echo "docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output --network none pdf-outline-extractor:v1.0"
    echo ""
    echo "The container will automatically process all PDFs from /app/input and generate corresponding JSONs in /app/output"
else
    echo "❌ Docker build failed!"
    exit 1
fi
