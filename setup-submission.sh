#!/bin/bash

# Setup script to create the exact directory structure required by the submission guidelines
echo "Setting up directory structure for submission compliance..."

# Create input directory and copy test files
mkdir -p input
mkdir -p output

# Copy test PDFs to input directory (as required by submission guidelines)
if [ -d "test_pdfs" ]; then
    echo "📂 Copying test PDFs to input/ directory..."
    cp test_pdfs/*.pdf input/ 2>/dev/null || echo "No PDF files found in test_pdfs/"
    
    # List what we copied
    pdf_count=$(ls input/*.pdf 2>/dev/null | wc -l)
    echo "✅ Copied $pdf_count PDF files to input/ directory"
    
    if [ $pdf_count -gt 0 ]; then
        echo "📄 Files in input directory:"
        ls -la input/
    fi
else
    echo "⚠️  test_pdfs directory not found. Please add PDF files to input/ directory manually."
fi

echo ""
echo "📋 Directory structure (required for submission):"
echo "   ./input/           <- Place your PDF files here"
echo "   ./output/          <- JSON results will appear here"
echo ""
echo "🐳 Docker commands (as per submission requirements):"
echo "   Build: docker build --platform linux/amd64 -t mysolutionname:somerandomidentifier ."
echo "   Run:   docker run --rm -v \$(pwd)/input:/app/input -v \$(pwd)/output:/app/output --network none mysolutionname:somerandomidentifier"
echo ""
echo "📝 What the container does:"
echo "   • Automatically processes all PDFs from /app/input directory"
echo "   • Generates corresponding filename.json in /app/output for each filename.pdf"
echo "   • Works offline (--network none compliance)"
echo "   • Uses AMD64 architecture"
echo ""
echo "✅ Setup complete! You can now:"
echo "   1. Add PDF files to ./input/ directory"
echo "   2. Run: ./build-docker.sh"
echo "   3. Run: ./run-docker.sh"
