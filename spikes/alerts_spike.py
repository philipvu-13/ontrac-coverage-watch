from bs4 import BeautifulSoup

with open("out/service-alerts.html", encoding="utf-8") as handle:
    soup = BeautifulSoup(handle.read(), "html.parser")

for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
    tag.decompose()

main = soup.find("main") or soup.body
text = " ".join(main.get_text(" ").split())

print("characters {}".format(len(text)))
print("")
print(text[:3000])