# My Document Title {.big-heading #top}

This is an introductory paragraph with a custom class. {.intro-paragraph}

This paragraph has both an id and multiple classes attached. {#p-main .highlight .callout}

## A Second Heading {.section-heading}

{.intro}
This is a paragraph with **bold**, *italic*, `code`, and a link: https://example.com.

- Bullet item
- Another item

- [ ] todo
- [x] done

- First item
- Second item
- Third item
{.fancy-list}

An inline image with classes:

![A small right-floated image](some-image.png){.right .small}

A code block with a language and extra class:

```python {.example-snippet .with-border}
def greet(name):
    print(f"Hello, {name}!")

greet("world")

# I am Header One
## I am Header Two
### I am Header Three
#### I am Header Four

A table:

| Col A | Col B |
| ----- | ----- |
| 1     | 2     |

A footnote reference.[^1]
[^1]: Footnote text.

Visit https://example.com or http://foo.test.
Email: someone@example.org

end
