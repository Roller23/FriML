(function() {
  let instruments = {};
  let context = new AudioContext();
  let envelope = context.createGain();
  Soundfont.instrument(context, 'bright_acoustic_piano', {release: 0, sustain: 1}).then(device => {
    instruments.piano = device;
    console.log('Piano loaded');
  });
  Soundfont.instrument(context, 'acoustic_guitar_nylon').then(device => {
    instruments.guitar = device;
    console.log('Guitar loaded');
  });
  Soundfont.instrument(context, 'violin').then(device => {
    instruments.violin = device;
    console.log('Violin loaded');
  });
  Soundfont.instrument(context, 'synth_bass_1').then(device => {
    instruments.synth = device;
    console.log('Synth loaded');
  });

  let get = selector => document.querySelector(selector);
  let getAll = selector => document.querySelectorAll(selector);

  HTMLElement.prototype.on = function(event, fn) {
    this.addEventListener(event, fn);
    return this;
  }

  NodeList.prototype.on = function(event, fn) {
    this.forEach(node => {
      node.on(event, fn);
    });
    return this;
  }

  function drawLine(from, length) {
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.moveTo(from.x, from.y + i);
      ctx.lineTo(from.x + length, from.y + i);
      ctx.strokeStyle = '#FFF';
      ctx.stroke();
    }
  }

  function clearTrack() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
  }

  function req(path, data) {
    return new Promise(resolve => {
      let xhr = new XMLHttpRequest();
      let form = new FormData();
      Object.keys(data).forEach(key => form.append(key, data[key]));
      const query = ('?') + new URLSearchParams(form).toString();
      xhr.onload = function(x) {
        try {
          let json = JSON.parse(this.responseText);
          json.song = JSON.parse(json.song);
          resolve(json);
        } catch (e) {
          console.log('Error!', this.responseText);
          resolve(null);
        }
      };
      xhr.open('GET', path + query, true);
      xhr.send();
    });
  }

  let canvas = get('canvas');
  let ctx = canvas.getContext('2d');
  let optimalScreenHeight = 800;

  getAll('.tick').forEach((tick, i) => {
    let rotation = i * (360 / 12);
    tick.setAttribute('rotation', rotation);
  });

  getAll('.tick .node').on('click', setKey);

  let selectedGenre = null;
  let selectedKey = null;
  let selectedInstrument = null;

  getAll('.genre').on('click', function(e) {
    selectedGenre = this.getAttribute('genre');
    get('.genres').classList.add('hidden');
    get('.keys').classList.remove('waiting');
    get('.line .dot.selected').classList.remove('selected');
    getAll('.line .dot')[1].classList.add('selected');
    let outerNodes = getAll('.outer > .tick > .node');
    let innerNodes = getAll('.inner > .tick > .node');
    setTimeout(function() {
      getAll('.outer > .tick').forEach((tick, i) => {
        let rotation = tick.getAttribute('rotation');
        tick.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
        outerNodes[i].style.transform = `translate(-50%, -50%) rotate(${-rotation}deg)`;
      });
      setTimeout(function() {
        getAll('.inner > .tick').forEach((tick, i) => {
          let rotation = tick.getAttribute('rotation');
          tick.style.transform = `translateX(-50%) rotate(${rotation}deg)`;
          innerNodes[i].style.transform = `translate(-50%, -50%) rotate(${-rotation}deg)`;
        });
      }, 100);
    }, 600);
  });

  getAll('.instruments > .instrument').on('click', setInstrument);

  function setKey() {
    get('.line .dot.selected').classList.remove('selected');
    getAll('.line .dot')[2].classList.add('selected');
    selectedKey = this.getAttribute('key');
    get('.slider > .keys').classList.add('hidden');
    get('.slider > .instruments').classList.remove('waiting');
  }

  async function setInstrument() {
    get('.line .dot.selected').classList.remove('selected');
    getAll('.line .dot')[3].classList.add('selected');
    selectedInstrument = this.getAttribute('name');
    get('.slider > .instruments').classList.add('hidden');
    get('.slider > .results').classList.remove('waiting');
    get('.slider').classList.add('expanded');
    console.log(selectedGenre, selectedKey, selectedInstrument);
    let data = {genre: selectedGenre, key: selectedKey, instrument: selectedInstrument};
    let json = await req('/data', data);
    if (json === null) return;
    console.log(json)
    get('.download-midi').setAttribute('href', '/outputs/' + json.song.name + '.mid')
    get('.download-wav').setAttribute('href', '/outputs/' + json.song.name + '.wav')
    songToPlay = transformMidi(json.song.notes);
    console.log('data', json)
  }

  function setDynamicSizes() {
    get('.results .bottom').style.width = `${300 * (document.body.clientHeight / optimalScreenHeight)}px`;
    let circleHeight = get('.circle.outer').scrollHeight * 0.1;
    let gapHeight = get('.circle.outer').scrollHeight * (0.25 / 4);
    getAll('.tick .node').forEach((node, i) => {
      node.style.height = circleHeight + 'px';
      node.style.lineHeight = circleHeight + 'px';
      node.style.width = circleHeight + 'px';
      node.style.marginTop = gapHeight + 'px';
    });
  }

  window.addEventListener('resize', setDynamicSizes);

  setDynamicSizes();

  class Note {
    constructor(_x, _duration, _pitch) {
      this.x = _x;
      this.duration = _duration;
      this.pitch = _pitch;
    }
  }

  function transformMidi(midi) {
    let result = [];
    let timePassed = 0;
    let speed = 1;
    midi.forEach(note => {
      timePassed += Math.floor(eval(note.off) * speed * 1000);
      let duration = Math.floor(eval(note.dur) * speed * 1000);
      let pitches = note.note.split('.');
      pitches.forEach(pitch => {
        try {
          let octavianNote = new Octavian.Note(pitch.replace('-', 'b'));
          result.push(new Note(timePassed, duration, octavianNote.pianoKey + 20));
        } catch (e) {
          console.log("Couldn't convert", note);
        }
      });
    });
    console.log('transformation result', result)
    return result;
  }

  let songToPlay = null;
  let songPlaying = false;
  let timeStart = -1;
  let timeouts = []

  function step(timestamp) {
    if (!songPlaying) return;
    if (timeStart === -1) {
      timeStart = timestamp;
      return window.requestAnimationFrame(step);
    }
    let progress = timestamp - timeStart;
    clearTrack();
    songToPlay.forEach(note => {
      let pos = {x: note.x - progress, y: note.pitch * 4};
      let length = note.duration;
      drawLine(pos, length);
    });
    window.requestAnimationFrame(step);
  }

  function startSong(e) {
    if (songPlaying) return;
    songPlaying = true;
    songToPlay.forEach((note, i) => {
      let timeout = setTimeout(() => {
        let playData = {duration: note.dur / 1000};
        // instruments.piano.play(note.pitch, context.currentTime, playData);
        instruments[selectedInstrument].play(note.pitch);
        console.log('playing', note);
        if (i === songToPlay.length - 1) {
          setTimeout(() => {
            songPlaying = false;
            timeStart = -1;
          }, note.dur + 500);
        }
      }, note.x);
      timeouts.push(timeout)
    });
    window.requestAnimationFrame(step);
  }

  get('.controls .play').on('click', startSong);

  get('.controls .replay').on('click', e => {
    if (!songPlaying) return;
    songPlaying = false;
    timeouts.forEach(t => clearTimeout(t));
    timeStart = -1;
    timeouts = []
    startSong(null);
  });

})();