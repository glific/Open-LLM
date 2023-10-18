#!/bin/zsh

BASE_URL="http://localhost:8000/api/upload"
SECRET_KEY="sk_EXAMPLE_SECRET_KEY"
SOURCE_FOLDER="llm/data/sources/"

for file in $SOURCE_FOLDER*; do
    if [[ -f $file ]]; then
        curl -X POST \
             -H "Authorization: $SECRET_KEY" \
             -H "Content-Type: multipart/form-data" \
             -F "file=@$file" \
             $BASE_URL
    fi
done
