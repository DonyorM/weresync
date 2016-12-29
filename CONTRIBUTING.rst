############
Contributing
############


Bug Reports and Issues
======================

Please feel free to report any issues or bugs you encounter while using WereSync. Each issue is very much appreciated. When you submit an issue, be sure to include the following in your report:

* Version of WereSync
* Version and distribution of Linux system
* Python version
* The log file, placed in /var/log/weresync by default.
* Other relevant details, such as whether or not images were used.

Project Contribution
=================

Thanks for wanting to join us! We welcome contributions of all types including code, documentation updates, and other process.

Basic Process
-------------

1. `Fork <https://help.github.com/articles/fork-a-repo/>`_ the project on GitHub
2. Clone your fork with `git clone <repository>`
3. Add your code to your fork. We recommend creating a new branch when you start your own code.
4. Tidy up your commits. WereSync accepts pull requests with multiple commits, but please make sure each commit deals with a significant part of the project. If you have a commit just fixing typos, squash that one into a more major commit. For information on how to do that see `here <http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html>`_.
5. Submit a `pull request <https://github.com/DonyorM/weresync/pulls>`_ merging your code into the `develop <https://github.com/DonyorM/weresync/tree/develop>`_ branch of WereSync
   * If your code is the first step on a new major feature, you could ask to create a new branch, allowing others to help you without affecting the main branch. Generally this is not required.
6. Keep an eye on your pull requests and respond to any requests for changes or updates.

Branches
--------

Do whatever you want as far as branches go on your own system, but WereSync does have some specific conventions as far as what branches to push to. The master branch contains only hotfixes and release code, new features go in the develop branch until they have been tested are ready for release.

Sometimes, a feature that is being worked on over a long period of time, such as the gui, might have its own branch. Take a look at branches before you start so you don't reinvent someone else's work. Your contributions are still very much welcome!

Tests
-----

WereSync's code is hard to unit test in many ways, because block devices are
complex and difficult to mock. However, if your code can be tested, possibly using mocks, you should add tests to your commit. Take a look at the code in the tests directory to see some examples. However, a 100% test coverage is not expected.

Style
-----

WereSync does not currently have a official style guide. Generally follow good
Python style practices and do what the rest of the code base does.
