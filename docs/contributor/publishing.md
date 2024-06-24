# Publishing Tianocore Edk2 PyTool Library (edk2toollib)

The __edk2toollib__ is published as a pypi (pip) module.  The pip module is
named __edk2-pytool-library__.  Pypi allows for easy version management,
dependency management, and sharing.

Publishing/releasing a new version is generally handled thru a server based
build process but for completeness the process is documented here.

## Version Scheme

Versioning follows: aa.bb.cc and is based on tags in git

* aa == Major version.  Changes don’t need to be backward compatible
* bb == Minor version.  Significant new features.  Backward compatibility
  generally maintained except when new feature is used.
* cc == Patch version.  Bug fix or small optional feature.  Backward
  compatibility maintained.

## Github Publishing Process

1. Navigate to the [Releases](https://github.com/tianocore/edk2-pytool-library/releases)
 section on the main page of edk2-pytool-library
2. Select `Draft a new release` at the top right of the page
3. Click `Choose a tag` and create the new release version (`v0.21.8`, `v0.22.0`, etc.)
4. Click `Generate release notes`
5. Add a new section `## Dependency Updates`
6. If the major / minor is rolled in this release, add a `## Integration Steps`
   section
6. Move all dependabot contributions to the `## Dependency Updates` section
7. Leave all "true" contributions in the `## What's Changed` section
7. Copy the integration steps from the pull request into the
   `## Integration Steps` section
8. Click `Publish release`

NOTE: Feel free to add additional sections to the release notes as necessary.
The release is not immediate. A pipeline will be queued that will perform final
CI checks and then release to pypi. You can monitor this pipeline [HERE](https://dev.azure.com/tianocore/edk2-pytools-library/_build?definitionId=3)


## Manual Publishing Process

NOTE: These directions assume you have already configured your workspace for
developing.  If not please first do that.  Directions on the
[developing](developing.md) page.

1. Pass all development tests and checks.
2. Update the __readme.md__ `Release Version History` section with info on all
   important changes for this version.  Remove the "-dev" tag from the version
   about to be released.
3. Get your changes into master branch (official releases should only be done
   from the master branch)
4. Make a git tag for the version that will be released and push tag.  Tag
   format is v\<Major>.\<Minor>.\<Patch>
5. Do the release process

    1. Install tools

        ``` cmd
        pip install --upgrade -e [publish]
        ```

    2. Build a wheel

        ``` cmd
        python -m build --sdist --wheel
        ```

    3. Confirm wheel version is aligned with git tag

        ``` cmd
        ConfirmVersionAndTag.py
        ```

    4. Publish the wheel/distribution to pypi

        ``` cmd
        twine upload dist/*
        ```
