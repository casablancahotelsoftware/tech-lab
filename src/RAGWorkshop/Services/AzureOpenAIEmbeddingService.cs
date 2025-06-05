using Azure;
using RAGWorkshop.Abstraction;
using Azure.AI.Inference;

namespace RAGWorkshop.Services
{
    public class AzureOpenAIEmbeddingService : IEmbeddingService
    {
        private readonly EmbeddingsClient _azureOpenAIClient;

        public AzureOpenAIEmbeddingService(EmbeddingsClient azureOpenAIClient)
        {
            _azureOpenAIClient = azureOpenAIClient;
        }

        public async Task<float[]> GenerateEmbeddingAsync(string content)
        {
            EmbeddingsOptions options = new EmbeddingsOptions(new List<string> { content });

            Response<EmbeddingsResult> response = await _azureOpenAIClient.EmbedAsync(options);

            foreach (EmbeddingItem result in response.Value.Data)
            {
                List<float>? embeddingList = result.Embedding.ToObjectFromJson<List<float>>();
                if (embeddingList != null)
                {
                    return embeddingList.ToArray();
                }
            }
            return Array.Empty<float>();
        }
    }
}
