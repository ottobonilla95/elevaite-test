from elevaitelib.schemas.configuration import EmbeddingType
from .base_embedding import (
    register_embedding,
)
from .local_embedding import (
    LocalEmbedding,
)
from .openai_embedding import (
    OpenAIEmbedding,
)


register_embedding(EmbeddingType.LOCAL, LocalEmbedding)
register_embedding(EmbeddingType.OPENAI, OpenAIEmbedding)
