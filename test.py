from PIL import Image
import requests
from modelscope import ChineseCLIPProcessor, ChineseCLIPModel

model = ChineseCLIPModel.from_pretrained('./models/OFA-Sys/chinese-clip-vit-huge-patch14')
processor = ChineseCLIPProcessor.from_pretrained('./models/OFA-Sys/chinese-clip-vit-huge-patch14')

url = "https://clip-cn-beijing.oss-cn-beijing.aliyuncs.com/pokemon.jpeg"
image = Image.open(requests.get(url, stream=True).raw)
# Squirtle, Bulbasaur, Charmander, Pikachu in English
texts = ["杰尼龟", "妙蛙种子", "小火龙", "皮卡丘"]

# compute image feature
inputs = processor(images=image, return_tensors="pt")
outputs = model.get_image_features(**inputs)
if hasattr(outputs, 'pooler_output'):
    image_embeds = outputs.pooler_output
else:
    image_embeds = outputs
image_features = image_embeds / image_embeds.norm(p=2, dim=-1, keepdim=True)  # normalize

# compute text features
inputs = processor(text=texts, padding=True, return_tensors="pt")
outputs = model.get_text_features(**inputs)
if hasattr(outputs, 'pooler_output'):
    text_embeds = outputs.pooler_output
else:
    text_embeds = outputs
text_features = text_embeds / text_embeds.norm(p=2, dim=-1, keepdim=True)  # normalize

similarity_scores = image_features @ text_features.T

# similarity_scores = (image_features @ text_features.T) / ( image_features * text_features)


print("图像与各文本的相似度分数：\n", similarity_scores)

# logit_scale = model.logit_scale.exp()  # CLIP自带的缩放系数
# logits = logit_scale * similarity_scores
# probs = logits.softmax(dim=1)

# print("概率：", probs)
# print("概率和：", probs.sum().item())  # 一定 = 1
# percentages = probs * 100

# 打印输出
# for i, prob in enumerate(probs[0]):
#     print(f"{texts[i]}: {prob.item()*100:.2f}%")


# compute image-text similarity scores
inputs = processor(text=texts, images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)
logits_per_image = outputs.logits_per_image  # this is the image-text similarity score
probs = logits_per_image.softmax(dim=1)  # probs: [[1.1419e-02, 1.0478e-02, 5.2018e-04, 9.7758e-01]]

print("图像-文本相似度分析结果")
print("=" * 50)

print("\n原始logits得分：")
for i, text in enumerate(texts):
    print(f"  {text}: {logits_per_image[0][i].item():.4f}")

print("\n相似度概率分布：")
for i, text in enumerate(texts):
    prob = probs[0][i].item()
    bar = "█" * int(prob * 40)
    print(f"  {text}: {prob:.4f} {bar}")

print(f"\n预测结果: {texts[probs[0].argmax().item()]}")
print("=" * 50)