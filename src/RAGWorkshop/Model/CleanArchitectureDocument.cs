using Microsoft.Extensions.VectorData;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;

namespace RAGWorkshop.Model
{
    /// <summary>
    /// Represents a processed document from the CleanArchitecture repository
    /// that can be stored in Semantic Kernel vector stores.
    /// </summary>
    public class CleanArchitectureDocument
    {
        [VectorStoreKey]
        public Guid Id { get; set; }

        [VectorStoreData(IsFullTextIndexed = true)]
        public string Content { get; set; } = string.Empty;

        [VectorStoreData(IsIndexed = true)]
        public string FilePath { get; set; } = string.Empty;

        [VectorStoreData(IsIndexed = true)]
        public string FileType { get; set; } = string.Empty;

        [VectorStoreData]
        public int TokenCount { get; set; }

        [VectorStoreData]
        public int ChunkIndex { get; set; }

        [VectorStoreData]
        public int TotalChunks { get; set; }
        [VectorStoreData]
        public string CreatedAt { get; set; } = DateTime.UtcNow.ToString("o");

        [VectorStoreVector(3072, DistanceFunction = DistanceFunction.CosineSimilarity, IndexKind = IndexKind.Hnsw)]
        public ReadOnlyMemory<float>? ContentEmbedding { get; set; }

        public static CleanArchitectureDocument FromJson(string json)
        {
            var data = JsonSerializer.Deserialize<JsonElement>(json);
            var metadata = data.GetProperty("metadata");

            return new CleanArchitectureDocument
            {
                Id = Guid.NewGuid(),
                Content = data.GetProperty("page_content").GetString() ?? string.Empty,
                FilePath = metadata.GetProperty("source").GetString() ?? string.Empty,
                FileType = metadata.GetProperty("file_type").GetString() ?? "unknown",
                TokenCount = metadata.GetProperty("token_count").GetInt32(),
                ChunkIndex = metadata.GetProperty("chunk_index").GetInt32(),
                TotalChunks = metadata.GetProperty("total_chunks").GetInt32(),
            };
        }
        private static List<string> GetStringList(JsonElement metadata, string propertyName)
        {
            if (metadata.TryGetProperty(propertyName, out var property) && property.ValueKind == JsonValueKind.Array)
            {
                return property.EnumerateArray().Select(x => x.GetString() ?? string.Empty).ToList();
            }
            return new List<string>();
        }
    }

}
