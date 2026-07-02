---
layout: archive
title: "Blog"
permalink: /blog/
author_profile: true
description: "Xiaoxiong Zhang's blog — notes on robot learning, world models, and large-scale pre-training."
---

{% include base_path %}

<p class="blog-intro">Notes on robot learning, world models, and things I'm figuring out along the way.</p>

{% if site.posts.size == 0 %}
<p class="blog-empty">No posts yet — check back soon.</p>
{% endif %}

<div class="blog-list">
{% capture written_year %}{% endcapture %}
{% for post in site.posts %}
  {% capture year %}{{ post.date | date: '%Y' }}{% endcapture %}
  {% if year != written_year %}
    <h3 class="blog-year">{{ year }}</h3>
    {% capture written_year %}{{ year }}{% endcapture %}
  {% endif %}
  <article class="blog-item">
    <time class="blog-item__date" datetime="{{ post.date | date_to_xmlschema }}">{{ post.date | date: "%b %-d, %Y" }}</time>
    <h2 class="blog-item__title"><a href="{{ base_path }}{{ post.url }}">{{ post.title }}</a></h2>
    {% if post.excerpt %}<p class="blog-item__excerpt">{{ post.excerpt | markdownify | strip_html | strip_newlines | truncate: 200 }}</p>{% endif %}
    {% if post.tags %}<div class="blog-item__tags">{% for tag in post.tags %}<span class="blog-tag">{{ tag }}</span>{% endfor %}</div>{% endif %}
  </article>
{% endfor %}
</div>
