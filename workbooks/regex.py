
import re

input_string = "abc𝓐𝓵𝓮𝔁𝓪𝓷𝓭𝓮𝓻abc"

# Define the regex pattern for allowed characters
pattern = r'[^a-zA-Z0-9_-]'

# Replace any character that doesn't match the pattern with an empty string
pattern = r'[^a-zA-Z0-9_-]'
username = re.sub(pattern, '', username)

print(filtered_string)