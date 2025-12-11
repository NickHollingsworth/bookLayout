{#top .big-heading}
# My Document Title

{.intro-paragraph}
This is an introductory paragraph with a custom class applied via a block
attribute on the line above.

{#p-main .highlight .callout}
This paragraph has both an id and multiple classes attached to it.

## A Second Heading

{.fancy-list}
- First item
- Second item
- Third item

Here is an image with inline attributes:

![A small right-floated image](some-image.png){.right .small}

A code block with extra classes attached to the `<code>` element:

{.example-snippet .with-border}
```python
def greet(name):
    print(f"Hello, {name}!")

greet("world")

