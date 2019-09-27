#!/usr/bin/python3

import csv
import click
import collections
import itertools
import logging
import sys

import bandplan
import schema

LOG = logging.getLogger(__name__)

HMK_HEADER = '''KENWOOD MCP FOR AMATEUR MOBILE TRANSCEIVER
[Export Software]=MCP-2A Version 3.22
[Export File Version]=1
[Type]=K
[Language]=English

// Coments
!! Comments=

// Memory Channels
!!Ch,Rx Freq.,Rx Step,Offset,T/CT/DCS,TO Freq.,CT Freq.,DCS Code,Shift/Split,Rev.,L.Out,Mode,Tx Freq.,Tx Step,M.Name
'''


def remove_empty_fields(fields):
    return {
        field: value
        for field, value in fields.items()
        if value is not None
        and (not isinstance(value, str) or value.strip() != '')
    }


@click.command()
@click.option('-v', '--verbose', count=True)
@click.option('-i', '--input', type=click.File('r'), default=sys.stdin)
@click.option('-o', '--output', type=click.File('w'), default=sys.stdout)
@click.option('-b', '--band', multiple=True)
@click.option('-s', '--state', multiple=True)
@click.option('-S', '--start-index', default=0)
@click.option('-m', '--mode', default='fm')
@click.option('--offline', is_flag=True)
def main(verbose, input, output, band, state, start_index, mode, offline):

    try:
        loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    except IndexError:
        loglevel = 'DEBUG'

    logging.basicConfig(level=loglevel)

    output.write(HMK_HEADER)

    channel = itertools.count(start_index)
    with input, output:
        repeaters = csv.DictReader(
            input,
            fieldnames=list(schema.NER_Channel.declared_fields.keys()))
        hmk = csv.DictWriter(
            output,
            fieldnames=['channel'] +
            list(schema.Kenwood_Channel.declared_fields.keys()))

        for row in repeaters:
            row = remove_empty_fields(row)
            ner, errors = schema.NER_Channel.load(row)

            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        LOG.error('reading %s: %s: %s',
                                  row['callsign'], fname, msg)
                continue

            if ner.get('status') == 'OFF' and not offline:
                continue

            if state:
                state = [s.lower() for s in state]
                if ner['state'].lower() not in state:
                    LOG.info('skipping %s: state %s not in %s',
                             ner['callsign'], ner['state'].lower(), state)
                    continue

            freq_band = bandplan.freq_to_band(ner['rx_freq'])
            if band:
                band = [b.lower() for b in band]
                if freq_band.name.lower() not in band:
                    LOG.info('skipping %s: frequency %0.3f not in %s',
                             ner['callsign'], ner['rx_freq'], band)
                    continue

            if mode:
                modes = [m.lower() for m in ner['mode']]
                if mode not in modes:
                    LOG.info('skipping %s: mode %s not in %s',
                             ner['callsign'], mode, modes)
                    continue

            LOG.debug('%s: modes: %s',
                      ner['callsign'], ner['mode'])

            tone_mode = 'T' if ner.get('tx_tone') else 'Off'
            if ner['offset'] == '-':
                offset_dir = '-'
            elif ner['offset'] == '+':
                offset_dir = '+'
            else:
                offset_dir = ' '

            ken, errors = schema.Kenwood_Channel.load(dict(
                rx_freq=ner['rx_freq'],
                tx_freq=ner['rx_freq'],
                rx_step=freq_band.step,
                tx_step=freq_band.step,
                offset=freq_band.offset,
                tone_mode=tone_mode,
                tone_freq=ner.get('tx_tone'),
                ct_freq=ner.get('rx_tone'),
                dcs_code=0,
                shift=offset_dir,
                mode='FM',
                name=ner['callsign'][:6]
            ))

            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        LOG.error('converting %s: %s: %s',
                            row['callsign'], fname, msg)
                continue

            row_out, errors = schema.Kenwood_Channel.dump(ken)
            if (errors):
                for fname, messages in errors.items():
                    for msg in messages:
                        LOG.error('writing %s: %s: %s',
                            row['callsign'], fname, msg)
                continue

            row_out['channel'] = next(channel)
            hmk.writerow(row_out)


if __name__ == '__main__':
    main()
