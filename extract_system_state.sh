#!/bin/bash
# Gogs State Extractor - Extract complete system state including code

echo "🚀 Gogs Complete State Extractor"
echo "================================="
echo

python3 /extract_complete_backup.py

echo
echo "✅ Extraction completed!"
echo "📁 Files created:"
echo "   - /complete_backup.json (JSON format)"
echo "   - /complete_backup.tar.gz (compressed)"
echo
echo "💾 To copy files out of container:"
echo "   docker cp <container>:/complete_backup.json ."
echo "   docker cp <container>:/complete_backup.tar.gz ."
