TEMPLATES = \
    all-users.html.j2 \
    database.html.j2 \
    error.html.j2 \
    index.html.j2 \
    new-user-token.html.j2 \
    no-user.html.j2 

prefix ?= /usr/local
datadir ?= $(prefix)/share

install:
	install -Dm 0755 app.py $(DESTDIR)$(datadir)/bitbake-hashserver-web-ui/app.py
	sed -i -e 's,@datadir@,$(datadir),g' $(DESTDIR)$(datadir)/bitbake-hashserver-web-ui/app.py
	for t in $(TEMPLATES); do \
		install -Dm 0644 templates/$$t $(DESTDIR)$(datadir)/bitbake-hashserver-web-ui/templates/$$t; \
	done
