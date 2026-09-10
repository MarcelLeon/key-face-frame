const scene = document.querySelector('#selected-scene');
const counter = document.querySelector('#scene-number');
const frames = [...document.querySelectorAll('[data-frame]')];
const descriptions = ['虚构人物在海边夕阳下的远景画面', '虚构人物在海边夕阳下的侧身画面', '虚构人物在海边夕阳下的特写画面'];
frames.forEach((button, index) => {
  button.addEventListener('click', () => {
    scene.style.backgroundPosition = `${index * 50}% 0%`;
    scene.setAttribute('aria-label', descriptions[index]);
    counter.textContent = `FRAME 0${index + 1} / 03`;
    frames.forEach((frame) => {
      const selected = frame === button;
      frame.classList.toggle('active', selected);
      frame.setAttribute('aria-pressed', String(selected));
    });
  });
  button.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    const next = frames[(index + (event.key === 'ArrowRight' ? 1 : 2)) % frames.length];
    next.focus();
    next.click();
  });
});
