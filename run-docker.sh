#!/bin/bash

# Run the PDF Outline Extractor with the exact command structure required
echo "Running PDF Outline Extractor..."

# Check if input directory exists (using 'input' as specified in requirements)
if [ ! -d "input" ]; then
    echo "❌ input directory not found. Please ensure you have PDFs to process in ./input/"
    echo "   Expected structure:"
    echo "   ./input/document1.pdf"
    echo "   ./input/document2.pdf" 
    echo "   ..."
    exit 1
fi

# Create output directory if it doesn't exist
mkdir -p output

echo "📁 Input directory: $(pwd)/input"
echo "📁 Output directory: $(pwd)/output"
echo "🐳 Running with network isolation (--network none)"

# Run the container with the exact command structure specified in requirements
docker run --rm \
    -v $(pwd)/input:/app/input \
    -v $(pwd)/output:/app/output \
    --network none \
    pdf-outline-extractor:v1.0

if [ $? -eq 0 ]; then
    echo "✅ Processing complete! Check the output/ directory for results."
    echo ""
    echo "Generated files:"
    ls -la output/*.json 2>/dev/null || echo "No JSON files generated (check for errors above)"
else
    echo "❌ Processing failed!"
    exit 1
fi
