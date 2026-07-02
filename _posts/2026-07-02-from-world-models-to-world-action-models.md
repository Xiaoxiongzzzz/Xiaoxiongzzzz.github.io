---
title: "From World Models to World Action Models: A Tutorial"
date: 2026-07-02
tags:
  - world-models
  - robotics
  - survey
excerpt: "A concise tutorial on world models for robotics — how action-conditioned predictors grow into world action models that turn imagined futures into robot actions."
toc: false
---

Together with my collaborators, I wrote a short tutorial on world models for
robotics: **[From World Models to World Action Models: A Concise Tutorial for
Robotics](https://clearlab-sustech.github.io/WorldModelSurvey/)**. It's meant to
be a readable entry point into the area rather than an exhaustive survey.

**The short version.** A world model is an *action-conditioned predictor*: given
the current observation and an action, it predicts what happens next. We sort
existing approaches into **observation-space** and **state-space** models and
weigh their trade-offs — visual fidelity versus how usable the prediction is for
control. We then introduce **world action models**, which close the loop by
turning predicted futures into executable actions, and lay out four paradigms
for doing so, from *imagine-then-execute* to jointly modeling video and action.

If you're getting into this space, I hope the taxonomy saves you some reading.

**Read it:**
[Project page](https://clearlab-sustech.github.io/WorldModelSurvey/) ·
[PDF](https://clearlab-sustech.github.io/WorldModelSurvey/assets/Understanding_World_Models__A_Tutorial_Perspective.pdf) ·
[arXiv](https://arxiv.org/abs/2607.00836) ·
[Code](https://github.com/clearlab-sustech/WorldModelSurvey)
