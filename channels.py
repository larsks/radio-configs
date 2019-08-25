import click
import csv
import jinja2


def read_channels(path):
    channels = []
    with open(path) as fd:
        reader = csv.DictReader(fd)
        for row in reader:
            channels.append(row)

    return channels


@click.command()
@click.option('-o', '--output')
@click.option('-f', '--format',
              type=click.Choice([
                  'uv5r',
                  'gd77',
              ]),
              default='uv5r',
              )
@click.argument('channel_file')
def main(format, output, channel_file):
    channels = read_channels(channel_file)
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader('templates'))
    template = env.get_template(format)
    print(template.render(channels=channels))


if __name__ == '__main__':
    main()
