---
title: "Hello, Blog — A Formatting Playground"
date: 2026-07-02
tags:
  - meta
  - world-models
excerpt: "The first post here, and a quick tour of everything the blog can render — headings, math, code, tables, footnotes, and references. Feel free to edit or delete this starter."
toc: true
toc_sticky: true
---

This is a starter post. It exists mainly to show how a write-up looks on this
blog and to give you a template to copy. **Edit it or delete it** — the file
lives at `_posts/2026-07-02-hello-blog.md`.

To publish a new post, drop a Markdown file into `_posts/` named
`YYYY-MM-DD-your-title.md`, give it the front matter above, and push. That's it.

## Text and structure

You get the usual Markdown: **bold**, *italic*, `inline code`, and
[links](https://xiaoxiongzzzz.github.io/). Lists work too:

- Learning from in-the-wild human videos
- World models and world action models
- Large-scale pre-training

1. First you predict the future,
2. then you turn that prediction into an action.

> A world model is just an action-conditioned predictor of what happens next.
> The interesting question is how to *act* on it.

## Math

Inline math renders with MathJax, e.g. a policy $\pi_\theta(a \mid s)$ that maps
states to actions. Display equations get their own line:

$$
\mathcal{L}(\theta) = \mathbb{E}_{(s,a)\sim\mathcal{D}}
\big[\, \| f_\theta(s) - a \|_2^2 \,\big].
$$

## Code

Fenced code blocks are syntax-highlighted:

```python
import torch
import torch.nn as nn

class WorldActionModel(nn.Module):
    """Predict the next latent, then decode an action from it."""
    def __init__(self, dim: int = 512):
        super().__init__()
        self.dynamics = nn.GRU(dim, dim, batch_first=True)
        self.action_head = nn.Linear(dim, 7)  # 6-DoF + gripper

    def forward(self, z):
        z_next, _ = self.dynamics(z)
        return self.action_head(z_next)
```

## Tables

| Paradigm              | Predicts        | Acts via              |
| --------------------- | --------------- | --------------------- |
| Imagine-then-execute  | future frames   | a separate policy     |
| Joint video–action    | frames + action | one model             |

## Footnotes and references

You can cite things inline with a footnote[^tape] and collect full references
at the bottom.

## References

1. Zhang, Zhang, Pan, Zheng, Zhang. *Generative Visual Foresight Meets
   Task-Agnostic Pose Estimation in Robotic Table-top Manipulation.* CoRL 2025.
2. Zhang, Zeng, Zhang. *From World Models to World Action Models: A Concise
   Tutorial for Robotics.* arXiv, 2026.

[^tape]: This is a footnote — click the arrow to jump back up.
