import builtins
import prettyprinter

prettyprinter.install_extras(include=['attrs'])
prettyprinter.set_default_style("light")

builtins.pretty = prettyprinter.cpprint
