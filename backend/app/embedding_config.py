"""Embedding / vector search constants."""

# Matches OpenAI text-embedding-3-small / ada-002 and many compatible APIs.
EMBEDDING_DIMENSIONS = 1536

# Rough char budget for OpenAI-compatible embedding inputs (~8k tokens).
# We truncate rather than crash when a chunk is oversized.
MAX_EMBEDDING_CHARS = 28_000

# How many texts to send per /embeddings request.
EMBEDDING_BATCH_SIZE = 16
