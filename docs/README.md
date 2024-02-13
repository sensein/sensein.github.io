# The Group Website

This is the website of our academic research group at MIT.

This website is powered by Jekyll and some Bootstrap, Bootwatch. Go to 
*aboutwebsite.md*  to learn how to copy and modify this page for your purpose. 


A big thank you to https://github.com/mpa139/allanlab for setting up this 
framework.

### For local development:

```
cd docs
```

and then

```
docker run -p 4000:4000 -v $(pwd):/site bretfisher/jekyll-serve
```

if the above complains, you may want to delete the Gemfile.lock and rerun.