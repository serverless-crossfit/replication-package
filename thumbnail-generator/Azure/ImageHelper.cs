using System.IO;
using SixLabors.ImageSharp;
using SixLabors.ImageSharp.Formats;
using SixLabors.ImageSharp.PixelFormats;
using SixLabors.ImageSharp.Processing;
using System.Collections.Generic;

namespace ThumbnailGenerator.Azure
{
    public interface IImageHelper
    {
        Stream ResizeImage(Stream image);
    }

    public class ImageHelper : IImageHelper
    {
        public Stream ResizeImage(Stream image)
        {
            Stream imageSmall = new MemoryStream();
            IImageFormat format;
            using (Image<Rgba32> input = Image.Load<Rgba32>(image, out format))
            {
                var dimensions = imageDimensionsTable[ImageSize.Small];

                input.Mutate(x => x.Resize(dimensions.Item1, dimensions.Item2));
                input.Save(imageSmall, format);
            }

            return imageSmall;
        }

        public enum ImageSize { ExtraSmall, Small, Medium }

        private static Dictionary<ImageSize, (int, int)> imageDimensionsTable = new Dictionary<ImageSize, (int, int)>() {
            { ImageSize.ExtraSmall, (320, 200) },
            { ImageSize.Small,      (160, 90) },
            { ImageSize.Medium,     (800, 600) }
        };
    }

}
