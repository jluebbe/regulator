import builtins

import prettyprinter

prettyprinter.install_extras(include=['attrs'])
prettyprinter.set_default_style("light")

builtins.pretty = prettyprinter.cpprint

@prettyprinter.register_pretty('regulator.location.Location')
def pretty_location(value, ctx):
    return "Location({})".format(value)

@prettyprinter.register_pretty('regulator.decode.Type')
def pretty_decoder_type(value, ctx):
    return prettyprinter.pretty_call_alt(
            ctx,
            type(value),
            kwargs=(
                ('name', value.name),
                ('kind', value.kind),
                ('fields', list(reversed(value.fields))),
            )
    )

@prettyprinter.register_pretty('regulator.decode.Cluster')
def pretty_decoder_type(value, ctx):
    return prettyprinter.pretty_call_alt(
            ctx,
            type(value),
            kwargs=(
                ('name', value.name),
                ('size', value.size),
                ('types', value.types),
                ('registers', list(value.registers)),
                ('word_size', value.word_size),
            )
    )
