code.mapit.mysociety.org
========================

The gh-pages branch is [code.mapit.mysociety.org](http://code.mapit.mysociety.org),
the Jekyll-based static site running on GitHub Pages that is the documentation
for setting up / running MapIt.

## Installation

In the below you could of course run `sudo gem install` but I personally never
think that's a good idea. You must already have gem and git installed (you
probably do).

```
gem install --no-document --user-install github-pages
# Add ~/.gem/ruby/2.0.0/bin/ or similar to your $PATH
# Check you can run "jekyll"
git clone --recursive -b gh-pages https://github.com/mysociety/mapit mapit-pages
cd mapit-pages
```

If you only want to edit the *text* of the site, this is all you need. Run
`jekyll serve --watch` to run a webserver of the static site, and make changes
to the text you want.

The theme for this static site is in another repository, called
mysociety-docs-theme, included here as a submodule. If you want to edit the
CSS, you'll additionally need to install sass:

```
gem install --no-document --user-install sass
```

If you need to change the shared theme, you will need to do so and then update
the submodule. Compiling the CSS is like normal:

```
sass --style=compressed theme/sass/global.scss assets/css/global.min.css
```
