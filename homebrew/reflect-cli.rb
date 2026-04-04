class ReflectCli < Formula
  include Language::Python::Virtualenv

  desc "Repo-owned memory for AI coding agents"
  homepage "https://github.com/codeyogi911/reflect"
  url "https://github.com/codeyogi911/reflect/archive/refs/tags/v0.1.0.tar.gz"
  # sha256 will be filled automatically by the tap update workflow
  license "MIT"

  depends_on "python@3.12"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "Repo-owned memory", shell_output("#{bin}/reflect --help")
  end
end
