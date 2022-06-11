import json
import logging
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import pytest
from pytest_mock import MockerFixture
import datalad_installer
from datalad_installer import (
    ON_LINUX,
    ON_MACOS,
    ON_POSIX,
    ON_WINDOWS,
    DataladGitAnnexReleaseBuildInstaller,
    main,
)


def bin_path(binname):
    if ON_WINDOWS:
        return Path("Scripts", binname + ".exe")
    else:
        return Path("bin", binname)


@pytest.fixture(autouse=True)
def capture_all_logs(caplog):
    caplog.set_level(logging.DEBUG)


@pytest.mark.miniconda
def test_install_miniconda(tmp_path):
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
        ]
    )
    assert r == 0
    assert (miniconda_path / bin_path("conda")).exists()
    r = subprocess.run(
        [str(miniconda_path / bin_path("conda")), "create", "-n", "test", "-y"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    assert "conda activate test" in r.stdout


@pytest.mark.miniconda
def test_install_miniconda_autogen_path(monkeypatch):
    # Override TMPDIR with a path that will be cleaned up afterwards (We can't
    # use tmp_path here, as that's apparently always in the user temp folder on
    # Windows regardless of the external value of TMPDIR.)
    with tempfile.TemporaryDirectory() as newtmp:
        monkeypatch.setenv("TMPDIR", newtmp)
        tempfile.tempdir = None  # Reset cache
        r = main(
            [
                "datalad_installer.py",
                "miniconda",
                "--batch",
            ]
        )
        assert r == 0
        (miniconda_path,) = Path(newtmp).glob("dl-miniconda-*")
        assert (miniconda_path / bin_path("conda")).exists()
        r = subprocess.run(
            [str(miniconda_path / bin_path("conda")), "create", "-n", "test", "-y"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        assert "conda activate test" in r.stdout
    tempfile.tempdir = None  # Reset cache


@pytest.mark.miniconda
def test_install_env_write_file_miniconda_conda_env(tmp_path):
    env_write_file = tmp_path / "env.sh"
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "-E",
            str(env_write_file),
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "conda-env",
            "-n",
            "foo",
        ]
    )
    assert r == 0
    assert (miniconda_path / bin_path("conda")).exists()
    assert (miniconda_path / "envs" / "foo").exists()
    ewf_path = str(env_write_file)
    if ON_WINDOWS:
        ewf_path = "/" + ewf_path.replace("\\", "/").replace(":", "", 1)
        bash = r"C:\Program Files\Git\bin\bash.EXE"
    else:
        bash = "bash"
    r = subprocess.run(
        [
            bash,
            "-c",
            f"source {shlex.quote(ewf_path)} && conda info --json",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    info = json.loads(r.stdout)
    assert info["active_prefix_name"] == "foo"
    assert info["conda_prefix"] == str(miniconda_path)


@pytest.mark.miniconda
def test_install_miniconda_datalad(tmp_path):
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "datalad",
        ]
    )
    assert r == 0
    assert (miniconda_path / bin_path("conda")).exists()
    assert (miniconda_path / bin_path("datalad")).exists()


@pytest.mark.miniconda
def test_install_miniconda_conda_env_datalad(tmp_path):
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "conda-env",
            "-n",
            "foo",
            "datalad",
        ]
    )
    assert r == 0
    assert (miniconda_path / bin_path("conda")).exists()
    assert not (miniconda_path / bin_path("datalad")).exists()
    assert (miniconda_path / "envs" / "foo").exists()
    assert (miniconda_path / "envs" / "foo" / bin_path("datalad")).exists()


@pytest.mark.miniconda
def test_install_venv_miniconda_datalad(tmp_path):
    venv_path = tmp_path / "venv"
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "venv",
            "--path",
            str(venv_path),
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "datalad",
        ]
    )
    assert r == 0
    assert (venv_path / bin_path("python")).exists()
    assert not (venv_path / bin_path("datalad")).exists()
    assert (miniconda_path / bin_path("conda")).exists()
    assert (miniconda_path / bin_path("datalad")).exists()


@pytest.mark.miniconda
def test_install_venv_miniconda_conda_env_datalad(tmp_path):
    venv_path = tmp_path / "venv"
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "venv",
            "--path",
            str(venv_path),
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "conda-env",
            "-n",
            "foo",
            "datalad",
        ]
    )
    assert r == 0
    assert (venv_path / bin_path("python")).exists()
    assert not (venv_path / bin_path("datalad")).exists()
    assert (miniconda_path / bin_path("conda")).exists()
    assert not (miniconda_path / bin_path("datalad")).exists()
    assert (miniconda_path / "envs" / "foo").exists()
    assert (miniconda_path / "envs" / "foo" / bin_path("datalad")).exists()


def test_install_venv_datalad(tmp_path):
    venv_path = tmp_path / "venv"
    r = main(
        [
            "datalad_installer.py",
            "venv",
            "--path",
            str(venv_path),
            "datalad",
        ]
    )
    assert r == 0
    assert (venv_path / bin_path("python")).exists()
    assert (venv_path / bin_path("datalad")).exists()


@pytest.mark.skipif(
    sys.version_info[:2] < (3, 7), reason="dev pip no longer supports Python < 3.7"
)
def test_install_venv_dev_pip_datalad(tmp_path):
    venv_path = tmp_path / "venv"
    r = main(
        [
            "datalad_installer.py",
            "venv",
            "--path",
            str(venv_path),
            "--dev-pip",
            "datalad",
        ]
    )
    assert r == 0
    assert (venv_path / bin_path("python")).exists()
    assert (venv_path / bin_path("datalad")).exists()


@pytest.mark.miniconda
def test_install_miniconda_conda_env_venv_datalad(tmp_path):
    venv_path = tmp_path / "venv"
    miniconda_path = tmp_path / "conda"
    r = main(
        [
            "datalad_installer.py",
            "miniconda",
            "--batch",
            "--path",
            str(miniconda_path),
            "conda-env",
            "-n",
            "foo",
            "venv",
            "--path",
            str(venv_path),
            "datalad",
        ]
    )
    assert r == 0
    assert (venv_path / bin_path("python")).exists()
    assert (venv_path / bin_path("datalad")).exists()
    assert (miniconda_path / bin_path("conda")).exists()
    assert not (miniconda_path / bin_path("datalad")).exists()
    assert (miniconda_path / "envs" / "foo").exists()
    assert not (miniconda_path / "envs" / "foo" / bin_path("datalad")).exists()


@pytest.mark.ci_only
@pytest.mark.skipif(
    not ON_LINUX or shutil.which("apt-get") is None,
    reason="requires Debian-based system",
)
def test_install_neurodebian_sudo_ok(mocker):
    spy = mocker.spy(datalad_installer, "runcmd")
    r = main(["datalad_installer.py", "--sudo=ok", "neurodebian"])
    assert r == 0
    assert spy.call_args_list[-2] == mocker.call(
        "sudo", "apt-get", "install", "-qy", "neurodebian", env=mocker.ANY
    )
    assert spy.call_args_list[-2][1]["env"]["DEBIAN_FRONTEND"] == "noninteractive"
    assert spy.call_args_list[-1] == mocker.call("nd-configurerepo")
    r = subprocess.run(
        [
            "dpkg-query",
            "-Wf",
            "${db:Status-Abbrev}",
            "neurodebian",
        ],
        stdout=subprocess.PIPE,
        universal_newlines=True,
        check=True,
    )
    assert r.stdout == "ii "


@pytest.mark.ci_only
@pytest.mark.skipif(
    not ON_MACOS or shutil.which("brew") is None, reason="requires macOS with Homebrew"
)
def test_install_git_annex_brew(mocker):
    spy = mocker.spy(datalad_installer, "runcmd")
    r = main(["datalad_installer.py", "git-annex", "-m", "brew"])
    assert r == 0
    assert spy.call_args_list[-1] == mocker.call("brew", "install", "git-annex")
    assert shutil.which("git-annex") is not None


@pytest.mark.ghauth
@pytest.mark.parametrize(
    "ostype,ext",
    [
        ("ubuntu", ".deb"),
        ("macos", ".dmg"),
        ("windows", ".exe"),
    ],
)
def test_download_latest_git_annex_release_asset(
    ostype: str, ext: str, tmp_path: Path
) -> None:
    DataladGitAnnexReleaseBuildInstaller.download(
        ostype=ostype,
        target_dir=tmp_path,
        version=None,
    )
    (p,) = tmp_path.iterdir()
    assert p.is_file()
    assert p.suffix == ext
    assert p.stat().st_size >= (1 << 20)  # 1 MiB


@pytest.mark.ghauth
@pytest.mark.parametrize(
    "ostype,version,filename,size",
    [
        (
            "ubuntu",
            "8.20211231",
            "git-annex-standalone_8.20211231-1.ndall+1_amd64.deb",
            49966540,
        ),
        ("macos", "8.20211123", "git-annex_8.20211123_x64.dmg", 28809446),
        ("windows", "8.20211117", "git-annex-installer_8.20211117_x64.exe", 18156853),
    ],
)
def test_download_specific_git_annex_release_asset(
    ostype: str, version: str, filename: str, size: int, tmp_path: Path
) -> None:
    DataladGitAnnexReleaseBuildInstaller.download(
        ostype=ostype,
        target_dir=tmp_path,
        version=version,
    )
    (p,) = tmp_path.iterdir()
    assert p.is_file()
    assert p.name == filename
    assert p.stat().st_size == size


@pytest.mark.skipif(not ON_POSIX, reason="POSIX only")
def test_install_git_annex_remote_rclone_latest_from_github(tmp_path: Path) -> None:
    r = main(
        [
            "datalad_installer.py",
            "git-annex-remote-rclone",
            "-m",
            "DanielDent/git-annex-remote-rclone",
            "--bin-dir",
            str(tmp_path / "bin"),
        ]
    )
    assert r == 0
    (p,) = (tmp_path / "bin").iterdir()
    assert p.is_file()
    assert p.name == "git-annex-remote-rclone"
    assert p.stat().st_size >= 5120


@pytest.mark.skipif(not ON_POSIX, reason="POSIX only")
def test_install_git_annex_remote_rclone_specific_version_from_github(
    tmp_path: Path,
) -> None:
    r = main(
        [
            "datalad_installer.py",
            "git-annex-remote-rclone=0.5",
            "-m",
            "DanielDent/git-annex-remote-rclone",
            "--bin-dir",
            str(tmp_path / "bin"),
        ]
    )
    assert r == 0
    (p,) = (tmp_path / "bin").iterdir()
    assert p.is_file()
    assert p.name == "git-annex-remote-rclone"
    assert p.stat().st_size == 7120


@pytest.mark.ci_only
@pytest.mark.needs_sudo
@pytest.mark.skipif(not ON_POSIX, reason="POSIX only")
def test_install_git_annex_remote_rclone_latest_from_github_globally() -> None:
    r = main(
        [
            "datalad_installer.py",
            "--sudo=ok",
            "git-annex-remote-rclone",
            "-m",
            "DanielDent/git-annex-remote-rclone",
        ]
    )
    assert r == 0
    p = Path("/usr/local/bin/git-annex-remote-rclone")
    assert p.is_file()
    assert p.stat().st_size >= 5120


def test_install_latest_rclone_from_downloads(tmp_path: Path) -> None:
    r = main(
        [
            "datalad_installer.py",
            "rclone",
            "-m",
            "downloads.rclone.org",
            "--bin-dir",
            str(tmp_path / "bin"),
        ]
    )
    assert r == 0
    (p,) = (tmp_path / "bin").iterdir()
    assert p.is_file()
    if ON_WINDOWS:
        assert p.name == "rclone.exe"
    else:
        assert p.name == "rclone"
    assert p.stat().st_size >= (1 << 20)  # 1 MiB


def test_install_latest_rclone_from_downloads_with_manpage(tmp_path: Path) -> None:
    r = main(
        [
            "datalad_installer.py",
            "rclone",
            "-m",
            "downloads.rclone.org",
            "--bin-dir",
            str(tmp_path / "bin"),
            "--man-dir",
            str(tmp_path / "man"),
        ]
    )
    assert r == 0
    (p,) = (tmp_path / "bin").iterdir()
    assert p.is_file()
    if ON_WINDOWS:
        assert p.name == "rclone.exe"
    else:
        assert p.name == "rclone"
    assert p.stat().st_size >= (1 << 20)  # 1 MiB
    (m,) = (tmp_path / "man" / "man1").iterdir()
    assert m.is_file()
    assert m.name == "rclone.1"
    assert m.stat().st_size >= (1 << 20)  # 1 MiB


@pytest.mark.parametrize(
    "version,size",
    [
        pytest.param(
            "1.55.0",
            43130880,
            marks=pytest.mark.skipif(not ON_LINUX, reason="Linux only"),
        ),
        pytest.param(
            "v1.54.1",
            58878352,
            marks=pytest.mark.skipif(not ON_MACOS, reason="macOS only"),
        ),
        pytest.param(
            "1.56.2",
            44712960,
            marks=pytest.mark.skipif(not ON_WINDOWS, reason="Windows only"),
        ),
    ],
)
def test_install_rclone_version_from_downloads(
    mocker: MockerFixture, tmp_path: Path, version: str, size: int
) -> None:
    mocker.patch("platform.machine", return_value="x86_64")
    r = main(
        [
            "datalad_installer.py",
            f"rclone={version}",
            "-m",
            "downloads.rclone.org",
            "--bin-dir",
            str(tmp_path / "bin"),
        ]
    )
    assert r == 0
    (p,) = (tmp_path / "bin").iterdir()
    assert p.is_file()
    if ON_WINDOWS:
        assert p.name == "rclone.exe"
    else:
        assert p.name == "rclone"
    assert p.stat().st_size == size


@pytest.mark.ci_only
@pytest.mark.needs_sudo
@pytest.mark.skipif(not ON_POSIX, reason="POSIX only")
def test_install_latest_rclone_from_downloads_globally(mocker: MockerFixture) -> None:
    spy = mocker.spy(datalad_installer, "runcmd")
    r = main(
        [
            "datalad_installer.py",
            "--sudo=ok",
            "rclone",
            "-m",
            "downloads.rclone.org",
        ]
    )
    assert r == 0
    p = Path("/usr/local/bin/rclone")
    if spy.called:
        spy.assert_called_once_with("sudo", "mv", "-f", "--", mocker.ANY, str(p))
    assert p.is_file()
    assert p.stat().st_size >= (1 << 20)  # 1 MiB
