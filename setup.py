"""
Setup configuration shim for building platform-specific wheels containing pre-compiled Go binaries.
"""

from setuptools import setup
from wheel.bdist_wheel import bdist_wheel as _bdist_wheel


class PlatformBdistWheel(_bdist_wheel):
    """
    Garante que a wheel gerada receba as tags da plataforma alvo específica
    em vez da tag genérica 'any', empacotando os binários Go embutidos em src/bin/.
    """

    def finalize_options(self):
        super().finalize_options()
        # Marca a wheel como contendo binários compilados específicos da plataforma
        self.root_is_pure = False


if __name__ == "__main__":
    setup(
        cmdclass={
            "bdist_wheel": PlatformBdistWheel,
        },
        package_dir={"": "src"},
        package_data={
            "": ["bin/*", "bin/*.exe"],
        },
        include_package_data=True,
    )
