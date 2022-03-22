using Microsoft.Azure.WebJobs;
using Microsoft.WindowsAzure.Storage;
using Microsoft.Extensions.Configuration;
using Microsoft.WindowsAzure.Storage.Blob;

namespace ThumbnailGenerator.Azure
{
    public interface IBlobHelper
    {
        CloudBlockBlob GetCloudBlockBlob(ExecutionContext context, string containerName, string blobName);
    }

    public class BlobHelper : IBlobHelper
    {
        public CloudBlockBlob GetCloudBlockBlob(ExecutionContext context, string containerName, string blobName)
        {
            var storageAccount = GetCloudStorageAccount(context);
            var blobClient = storageAccount.CreateCloudBlobClient();
            var container = blobClient.GetContainerReference(containerName);
            var blob = container.GetBlockBlobReference(blobName);
            
            return blob;
        }

        private CloudStorageAccount GetCloudStorageAccount(ExecutionContext executionContext)
        {
            var config = new ConfigurationBuilder()
                            .SetBasePath(executionContext.FunctionAppDirectory)
                            .AddJsonFile("local.settings.json", true, true)
                            .AddEnvironmentVariables().Build();
            CloudStorageAccount storageAccount = CloudStorageAccount.Parse(config["CloudStorageAccount"]);
            return storageAccount;
        }
    }

}
