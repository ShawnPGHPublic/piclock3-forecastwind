"""Forecast column with wind drawn to the right of each cell's icon.

Same hours-then-days layout as Forecast.  Chance, accumulation and
temperature stay in the wx block.  Wind is current/gust with no unit.
"""
import logging

from PyQt5 import QtGui
from PyQt5.QtCore import Qt

from PiClock3.Widget import Widget

logger = logging.getLogger(__name__)


class ForecastWind(Widget):

    def __init__(self, piclock, name, config):
        super().__init__(piclock, name, config)
        self.provider = piclock.plugins[self.config['forecast-provider']]
        self.cells = []
        self.hourFormat = None
        self.dayFormat = None

    def start(self):
        self.hourFormat = self.strftimePortableFormat(
            self.piclock.expand(self.config['hour-format']))
        self.dayFormat = self.strftimePortableFormat(
            self.piclock.expand(self.config['day-format']))
        want = int(self.config['hourly']) + int(self.config['daily'])
        if want > len(self.regions):
            logger.warning(
                '%s asks for %d cells (%s hourly + %s daily) but its region'
                ' has %d', self.name, want, self.config['hourly'],
                self.config['daily'], len(self.regions))

        for region in self.regions:
            self.cells.append({
                'icon': self.part('icon', region),
                'wind': self.part('wind', region),
                'wx': self.part('wx', region),
                'day': self.part('day', region),
            })

        credit = self.provider.attribution
        if credit and 'attribution' in self.config['layout']:
            self.part('attribution', self.regions[-1]).setText(credit)

        self.provider.subscribe(self.draw)

    def pageChange(self):
        return

    def draw(self):
        hours = int(self.config['hourly'])
        days = int(self.config['daily'])
        near = self.provider.hourly(hours, int(self.config['hourly-step']))
        far = self.provider.daily(days)

        for i, cell in enumerate(self.cells):
            if i < hours and i < len(near):
                self.fill(cell, near[i], self.hourFormat,
                          self.hourFigures(near[i]))
            elif hours <= i < hours + days and (i - hours) < len(far):
                day = far[i - hours]
                self.fill(cell, day, self.dayFormat,
                          self.dayFigures(day))
            else:
                for key in ('icon', 'wind', 'wx', 'day'):
                    cell[key].clear()

    def fill(self, cell, entry, when, figures):
        p = QtGui.QPixmap(self.icon(entry['icon']))
        cell['icon'].setPixmap(p.scaled(
            cell['icon'].width(), cell['icon'].height(),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cell['wind'].setText(self.windLine(entry))
        cell['wx'].setText(
            self.piclock.condition(entry.get('condition'))
            + '\n' + figures)
        cell['day'].setText(entry['when'].strftime(when))

    def windLine(self, entry):
        """a compass point then current/gust, no unit."""
        speed, gust, heading = self.windValues(entry)
        if speed is None and gust is None and heading is None:
            return ''
        if gust is None:
            gust = speed
        if speed is None:
            speed = gust
        parts = []
        point = self.compass(heading)
        if point:
            parts.append(point)
        if speed is not None:
            parts.append(' %s/%s' % (self.speedNumber(speed),
                                    self.speedNumber(gust)))
        return ' '.join(parts)
    
    def compass(self, deg):
        if deg is None:
            return ''
        return self.units('direction', 'deg', deg)
        
    def speedNumber(self, kph):
        shown = self.units('speed', 'kph', kph)
        digits = ''.join(c for c in shown if c.isdigit() or c in '.-')
        if not digits:
            return ''
        try:
            return '%d' % int(round(float(digits)))
        except ValueError:
            return digits

    def windValues(self, entry):
        raw = entry.get('raw')
        slots = raw if isinstance(raw, list) else [raw] if raw else []
        speeds, gusts = [], []
        heading = entry.get('wind-dir')
        best_speed = None
        for slot in slots:
            if not isinstance(slot, dict):
                continue
            wind = slot.get('wind') or {}
            nested_speed = wind.get('speed')
            nested_gust = wind.get('gust')
            kph = None
            if nested_speed is not None:
                kph = float(nested_speed) * 3.6
                speeds.append(kph)
            if nested_gust is not None:
                gusts.append(float(nested_gust) * 3.6)
            if (kph is not None and wind.get('deg') is not None
                    and (best_speed is None or kph >= best_speed)):
                best_speed = kph
                heading = wind.get('deg')
        speed = entry.get('wind')
        gust = entry.get('gust')
        if speed is None and speeds:
            speed = max(speeds)
        if gust is None and gusts:
            gust = max(gusts)
        return speed, gust, heading

    def hourFigures(self, hour):
        return (self.chance(hour) + self.accumulation(hour) +
                self.temperature(hour['temp']))

    def dayFigures(self, day):
        return (self.chance(day) + self.accumulation(day) +
                self.temperature(day['high'], unit=False) + '/' +
                self.temperature(day['low'], unit=False))

    def chance(self, entry):
        pop = entry.get('precip')
        return '' if not pop else '%d%% ' % pop

    def accumulation(self, entry):
        snowy = entry['icon'] == 'snow'
        amount = entry.get('snow') if snowy else None
        frm = 'cm'
        if amount is None:
            amount, frm = entry.get('accum'), 'mm'
        if not amount:
            return ''
        shown = self.units('depth', frm, amount)
        if float(''.join(c for c in shown if c.isdigit() or c == '.')) == 0:
            return ''
        word = self.piclock.condition('SN' if snowy else 'RA')
        return '%s %s ' % (word, shown)

    def temperature(self, c, unit=True):
        if c is None:
            return ''
        t = self.units('temperature', 'C', c)
        return t if unit else t.rstrip('CF').rstrip('°')
