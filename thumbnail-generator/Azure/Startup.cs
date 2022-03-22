using Microsoft.ApplicationInsights.Extensibility;
using Microsoft.Azure.Functions.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection;
using ThumbnailGenerator.Azure;

[assembly: FunctionsStartup(typeof(FunctionApp.Startup))]

namespace FunctionApp
{
    public class Startup : FunctionsStartup
    {
        public override void Configure(IFunctionsHostBuilder builder)
        {
            // builder.Services.AddSingleton<IBlobHelper, BlobHelper>();
            // builder.Services.AddSingleton<IImageHelper, ImageHelper>();
            builder.Services.AddLogging();
        }
    }
}