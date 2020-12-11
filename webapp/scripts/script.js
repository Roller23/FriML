(function() {

  let instrument = null;
  let context = new AudioContext();
  let envelope = context.createGain();
  envelope.gain.value = 0.05;
  Soundfont.instrument(context, 'acoustic_grand_piano', {release: 5, sustain: 5}).then(device => {
    instrument = device;
    console.log('Piano loaded');
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
    for (let i = 0; i < 10; i++) {
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
    songToPlay = transformMidi(json.song);
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

  let dummyLines = [
    {x: 50, y: 50, length: 100},
    {x: 50, y: 70, length: 150},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 30},
    {x: 50, y: 200, length: 30},
    {x: 50, y: 170, length: 30},
    {x: 50, y: 150, length: 100},
    {x: 50, y: 130, length: 100},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 150},
    {x: 50, y: 50, length: 100},
    {x: 50, y: 70, length: 150},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 30},
    {x: 50, y: 200, length: 30},
    {x: 50, y: 170, length: 30},
    {x: 50, y: 150, length: 100},
    {x: 50, y: 130, length: 100},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 150},
    {x: 50, y: 50, length: 100},
    {x: 50, y: 70, length: 150},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 30},
    {x: 50, y: 200, length: 30},
    {x: 50, y: 170, length: 30},
    {x: 50, y: 150, length: 100},
    {x: 50, y: 130, length: 100},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 150},
    {x: 50, y: 50, length: 100},
    {x: 50, y: 70, length: 150},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 30},
    {x: 50, y: 200, length: 30},
    {x: 50, y: 170, length: 30},
    {x: 50, y: 150, length: 100},
    {x: 50, y: 130, length: 100},
    {x: 50, y: 100, length: 50},
    {x: 50, y: 50, length: 150},
  ];

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
    midi.forEach(note => {
      timePassed += Math.floor(eval(note.off) * 1000);
      let duration = Math.floor(eval(note.dur) * 1000);
      let pitches = note.note.split('.');
      pitches.forEach(pitch => {
        let octavianNote = new Octavian.Note(pitch.replace('-', 'b'));
        result.push(new Note(timePassed, duration, octavianNote.pianoKey));
      });
    });
    console.log('transformation result', result)
    return result;
  }

  let songToPlay = null;
  let songPlaying = false;
  let timeStart = -1;

  function step(timestamp) {
    if (timeStart === -1) {
      timeStart = timestamp;
      return window.requestAnimationFrame(step);
    }
    let progress = timestamp - timeStart;
    clearTrack();
    songToPlay.forEach(note => {
      let pos = {x: note.x - progress, y: note.pitch * 6};
      let length = note.duration;
      drawLine(pos, length);
    });
    window.requestAnimationFrame(step);
  }

  get('.controls .play').on('click', e => {
    if (songPlaying) return;
    songPlaying = true;
    songToPlay.forEach(note => {
      setTimeout(() => {
        let playData = {duration: note.dur / 1000};
        instrument.play(note.pitch, context.currentTime, playData);
        console.log('playing', note.pitch)
      }, note.x);
    });
    window.requestAnimationFrame(step);
  });

})();