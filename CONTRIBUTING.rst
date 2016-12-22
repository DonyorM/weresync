############
Contributing
############


Bug Reports and Issues
======================

Please feel free to report any issues or bugs you encounter while using WereSync. When you submit an issue, be sure to include the following in your report:

* Version of WereSync
* Version and distribution of Linux system
* Python version
* The log file, placed in /var/log/weresync by default.
* Other relevant details, such as whether or not images were used.

Code Contribution
=================

Thanks for wanting to join us! To contribute to WereSync first fork this repository, then clone to your own system. You can switch to the develop branch, make your adjustments, and then create a pull request.

Branches
--------

Do whatever you want as far as branches go on your own system, but WereSync does have some specific conventions as far as what branches to push to. The master branch contains only hotfixes and release code, new features go in the develop branch until they have been tested are ready for release.

Sometimes, a feature that is being worked on over a long period of time, such as the gui, might have its own branch. Take a look at branches before you start so you don't reinvent someone else's work. Your contributions are still very much welcome!

Tests
-----

WereSync's code is hard to unit test in many ways, because block devices are
complex and difficult to mock. However, if your code can be tested, possibly using mocks, you should add tests to your commit. Take a look at the code in the tests directory to see some examples. However, a 100% test coverage is not expected.


