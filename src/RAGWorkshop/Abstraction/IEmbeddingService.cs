using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace RAGWorkshop.Abstraction
{
    public interface IEmbeddingService
    {
        Task<float[]> GenerateEmbeddingAsync(string content);
    }
}
