.. Documentation on translating WereSync
.. include:: global.rst.inc

====================
Translating WereSync
====================

WereSync supports translation via Pythons
`gettext <https://docs.python.org/3/library/gettext.html#class-based-api>`_
module. For end users, if your language is supported, it will simply change
based on your system locale and requires no further configuration.

More languages are always welcome. If know another language besides English
your contribution would be most welcome. You can follow these steps in order
to translate WereSync.

1. Clone WereSync to your computer::

       $ git clone https://github.com/DonyorM/weresync.git

2. Enter the WereSync source directory::

       $ cd weresync/src

3. Generate the `weresync.pot` file with the `pygettext` command from within
   the "src" directory::

       $ pygettext -d weresync weresync/*.py weresync/plugins/*.py

4. Translate the file. I recommend using a tool, such as
   `poedit <https://poedit.net/>`_ to edit the translation. Be sure to choose
   the UTF-8 encoding.
5. Place your translation files in the proper folder. `gettext` expects
   specific path for language files::

       $ mkdir -p resources/locale/<lang_code>/LC_MESSAGES/weresync.po

   You can find your language code `here <https://www.gnu.org/software/gettext/manual/gettext.html#Language-Codes>`_.
6. Add your language code to the `LANGUAGES` list of the `interface` module.
7. Stage and commit your new language folder and the `interface.py` file.
   Then create and submit a pull request.
