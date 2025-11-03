import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import CustomCursor from '../components/CustomCursor';
import './LandingPage.css';

const LandingPage = () => {
  const navigate = useNavigate();
  const canvasRef = useRef(null);
  const eventHorizonRef = useRef(null);
  const [eventHorizonOpacity, setEventHorizonOpacity] = useState(0);
  const [starsVisible, setStarsVisible] = useState(false);
  const starsVisibleRef = useRef(false);
  const starsOpacityRef = useRef(0);
  const eventHorizonOpacityRef = useRef(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    const eventHorizonCanvas = eventHorizonRef.current;
    if (!canvas || !eventHorizonCanvas) return;

    const ctx = canvas.getContext('2d');
    const ehCtx = eventHorizonCanvas.getContext('2d');

    const minWidth = 1920;
    canvas.width = Math.max(window.innerWidth, minWidth);
    canvas.height = window.innerHeight;
    eventHorizonCanvas.width = Math.max(window.innerWidth, minWidth);
    eventHorizonCanvas.height = window.innerHeight;

    const stars = [];
    const starCount = 200;
    const horizonY = canvas.height * 0.85;

    const isInEventHorizon = (x, y) => {
      const centerX = canvas.width / 2;
      const distanceFromCenter = Math.abs(x - centerX);
      const normalizedDistance = distanceFromCenter / (canvas.width / 2);

      const curveHeight = 120;
      const curveY = horizonY - Math.cos(normalizedDistance * Math.PI / 2) * curveHeight;

      const threshold = 80;
      return y > curveY - threshold;
    };

    for (let i = 0; i < starCount; i++) {
      let x, y;
      let attempts = 0;
      do {
        x = Math.random() * canvas.width;
        y = Math.random() * canvas.height;
        attempts++;
      } while (isInEventHorizon(x, y) && attempts < 50);

      if (attempts < 50) {
        stars.push({
          x,
          y,
          radius: Math.random() * 1.5,
          opacity: Math.random(),
          speed: Math.random() * 0.5 + 0.1,
        });
      }
    }

    const drawEventHorizon = (opacity = 1, revealProgress = 1) => {
      ehCtx.clearRect(0, 0, eventHorizonCanvas.width, eventHorizonCanvas.height);

      const effectiveWidth = Math.max(window.innerWidth, 1920);
      const centerX = effectiveWidth / 2;
      const currentHorizonY = eventHorizonCanvas.height * 0.97;

      const curvePoints = [];
      for (let x = 0; x <= effectiveWidth; x += 2) {
        const distanceFromCenter = Math.abs(x - centerX);
        const normalizedDistance = distanceFromCenter / (effectiveWidth / 2);
        const curveHeight = 200;
        const y = currentHorizonY - Math.cos(normalizedDistance * Math.PI / 2) * curveHeight;
        curvePoints.push({ x, y });
      }

      ehCtx.save();
      ehCtx.globalAlpha = opacity;

      const drawLayer = (gradient, lineWidth, shadowBlur, offsetY = 0) => {
        const revealWidth = effectiveWidth * revealProgress;
        const startX = centerX - revealWidth / 2;
        const endX = centerX + revealWidth / 2;

        ehCtx.beginPath();
        let hasStarted = false;
        curvePoints.forEach((point, i) => {
          if (point.x >= startX && point.x <= endX) {
            if (!hasStarted) {
              ehCtx.moveTo(point.x, point.y + offsetY);
              hasStarted = true;
            } else {
              ehCtx.lineTo(point.x, point.y + offsetY);
            }
          }
        });
        ehCtx.strokeStyle = gradient;
        ehCtx.lineWidth = lineWidth;
        ehCtx.shadowBlur = shadowBlur;
        ehCtx.shadowColor = gradient;
        ehCtx.stroke();
      };

      const mainGradient = ehCtx.createLinearGradient(0, 0, effectiveWidth, 0);
      mainGradient.addColorStop(0, 'rgba(168, 85, 247, 0)');
      mainGradient.addColorStop(0.2, 'rgba(168, 85, 247, 0.9)');
      mainGradient.addColorStop(0.5, 'rgba(168, 85, 247, 1.0)');
      mainGradient.addColorStop(0.8, 'rgba(168, 85, 247, 0.9)');
      mainGradient.addColorStop(1, 'rgba(168, 85, 247, 0)');

      const midPurpleGradient = ehCtx.createLinearGradient(0, 0, effectiveWidth, 0);
      midPurpleGradient.addColorStop(0, 'rgba(192, 132, 252, 0)');
      midPurpleGradient.addColorStop(0.2, 'rgba(192, 132, 252, 0.9)');
      midPurpleGradient.addColorStop(0.5, 'rgba(192, 132, 252, 1.0)');
      midPurpleGradient.addColorStop(0.8, 'rgba(192, 132, 252, 0.9)');
      midPurpleGradient.addColorStop(1, 'rgba(192, 132, 252, 0)');

      const lightPurpleGradient = ehCtx.createLinearGradient(0, 0, effectiveWidth, 0);
      lightPurpleGradient.addColorStop(0, 'rgba(224, 168, 255, 0)');
      lightPurpleGradient.addColorStop(0.2, 'rgba(224, 168, 255, 0.9)');
      lightPurpleGradient.addColorStop(0.5, 'rgba(224, 168, 255, 1.0)');
      lightPurpleGradient.addColorStop(0.8, 'rgba(224, 168, 255, 0.9)');
      lightPurpleGradient.addColorStop(1, 'rgba(224, 168, 255, 0)');

      const whiteGradient = ehCtx.createLinearGradient(0, 0, effectiveWidth, 0);
      whiteGradient.addColorStop(0, 'rgba(255, 255, 255, 0)');
      whiteGradient.addColorStop(0.2, 'rgba(255, 255, 255, 0.9)');
      whiteGradient.addColorStop(0.5, 'rgba(255, 255, 255, 1.0)');
      whiteGradient.addColorStop(0.8, 'rgba(255, 255, 255, 0.9)');
      whiteGradient.addColorStop(1, 'rgba(255, 255, 255, 0)');

      drawLayer(mainGradient, 8, 40, -3);
      drawLayer(midPurpleGradient, 5, 30, -2);
      drawLayer(lightPurpleGradient, 3, 20, -1);
      drawLayer(whiteGradient, 5, 15, 0);

      ehCtx.globalCompositeOperation = 'screen';
      drawLayer(mainGradient, 10, 50, -3);
      drawLayer(lightPurpleGradient, 6, 35, -1);
      ehCtx.globalCompositeOperation = 'source-over';

      ehCtx.restore();
    };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      stars.forEach((star) => {
        star.opacity += star.speed * 0.02;
        if (star.opacity > 1 || star.opacity < 0) {
          star.speed = -star.speed;
        }

        ctx.beginPath();
        ctx.arc(star.x, star.y, star.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.abs(star.opacity) * starsOpacityRef.current})`;
        ctx.fill();
      });

      requestAnimationFrame(animate);
    };

    animate();

    const initialDelay = 1000;
    let animationStartTime = null;
    const eventHorizonDuration = 1200;
    const starsDelay = 800;
    const starsFadeInDuration = 800;

    const animateEventHorizon = () => {
      if (!animationStartTime) {
        const now = Date.now();
        if (now - Date.now() < initialDelay) {
          requestAnimationFrame(animateEventHorizon);
          return;
        }
        animationStartTime = now;
      }

      const elapsed = Date.now() - animationStartTime;
      const opacity = Math.min(elapsed / eventHorizonDuration, 1);
      const revealProgress = Math.min(elapsed / eventHorizonDuration, 1);

      eventHorizonOpacityRef.current = opacity;
      setEventHorizonOpacity(opacity);
      drawEventHorizon(opacity, revealProgress);

      if (elapsed >= starsDelay) {
        const starsElapsed = elapsed - starsDelay;
        const starsOpacity = Math.min(starsElapsed / starsFadeInDuration, 1);
        starsOpacityRef.current = starsOpacity;

        if (!starsVisibleRef.current && starsOpacity > 0) {
          starsVisibleRef.current = true;
          setStarsVisible(true);
        }
      }

      if (elapsed < eventHorizonDuration + starsDelay + starsFadeInDuration) {
        requestAnimationFrame(animateEventHorizon);
      }
    };

    setTimeout(() => {
      animationStartTime = Date.now();
      animateEventHorizon();
    }, initialDelay);

    const handleResize = () => {
      const minWidth = 1920;
      canvas.width = Math.max(window.innerWidth, minWidth);
      canvas.height = window.innerHeight;
      eventHorizonCanvas.width = Math.max(window.innerWidth, minWidth);
      eventHorizonCanvas.height = window.innerHeight;
      drawEventHorizon(eventHorizonOpacityRef.current, 1);
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="landing-page">
      <CustomCursor />
      <canvas ref={canvasRef} className="starfield" />
      <canvas ref={eventHorizonRef} className="event-horizon-canvas" />

      <div className="landing-content">
        <motion.div
          className="title-container"
          initial={{ opacity: 0, y: -50 }}
          animate={{ opacity: starsVisible ? 1 : 0, y: starsVisible ? 0 : -50 }}
          transition={{ duration: 1, delay: 0.5 }}
        >
          <h1 className="main-title">MovieVerse</h1>
          <p className="subtitle">Unfolding the universe of movies</p>
        </motion.div>

        <motion.button
          className="cta-button"
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: starsVisible ? 1 : 0, scale: starsVisible ? 1 : 0.8 }}
          transition={{ duration: 0.8, delay: 0.8 }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => navigate('/home')}
        >
          <span className="button-text">Getting Started</span>
        </motion.button>
      </div>
    </div>
  );
};

export default LandingPage;
