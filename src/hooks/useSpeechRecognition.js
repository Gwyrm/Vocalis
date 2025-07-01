import { useState, useEffect, useRef, useCallback } from 'react';

const useSpeechRecognition = (options = {}) => {
  const {
    continuous = true,
    interimResults = true,
    language = process.env.REACT_APP_SPEECH_LANG || 'fr-FR',
    onResult,
    onError,
    onEnd,
  } = options;

  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
  const [error, setError] = useState(null);
  const [isSupported, setIsSupported] = useState(false);

  const recognitionRef = useRef(null);
  const finalTranscriptRef = useRef('');

  useEffect(() => {
    // Check if speech recognition is supported
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    
    if (!SpeechRecognition) {
      setError('La reconnaissance vocale n\'est pas supportée par votre navigateur');
      setIsSupported(false);
      return;
    }

    setIsSupported(true);

    // Create recognition instance
    const recognition = new SpeechRecognition();
    recognition.continuous = continuous;
    recognition.interimResults = interimResults;
    recognition.lang = language;
    recognition.maxAlternatives = 1;

    // Handle results
    recognition.onresult = (event) => {
      let interimText = '';
      let finalText = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        const transcriptText = result[0].transcript;

        if (result.isFinal) {
          finalText += transcriptText + ' ';
        } else {
          interimText += transcriptText;
        }
      }

      if (finalText) {
        finalTranscriptRef.current += finalText;
        setTranscript(finalTranscriptRef.current);
        if (onResult) {
          onResult(finalTranscriptRef.current, finalText);
        }
      }

      setInterimTranscript(interimText);
    };

    // Handle errors
    recognition.onerror = (event) => {
      let errorMessage = 'Erreur de reconnaissance vocale';
      
      switch (event.error) {
        case 'no-speech':
          errorMessage = 'Aucune parole détectée';
          break;
        case 'audio-capture':
          errorMessage = 'Aucun microphone trouvé';
          break;
        case 'not-allowed':
          errorMessage = 'Accès au microphone refusé';
          break;
        case 'network':
          errorMessage = 'Erreur réseau';
          break;
        default:
          errorMessage = `Erreur: ${event.error}`;
      }

      setError(errorMessage);
      setIsListening(false);
      
      if (onError) {
        onError(event);
      }
    };

    // Handle end
    recognition.onend = () => {
      setIsListening(false);
      setInterimTranscript('');
      
      if (onEnd) {
        onEnd();
      }
    };

    // Handle start
    recognition.onstart = () => {
      setIsListening(true);
      setError(null);
    };

    recognitionRef.current = recognition;

    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [continuous, interimResults, language, onResult, onError, onEnd]);

  // Start listening
  const startListening = useCallback(() => {
    if (!isSupported || !recognitionRef.current) {
      setError('La reconnaissance vocale n\'est pas disponible');
      return;
    }

    if (isListening) {
      return;
    }

    try {
      recognitionRef.current.start();
    } catch (err) {
      if (err.message.includes('already started')) {
        // Already listening, ignore
        return;
      }
      setError(`Erreur au démarrage: ${err.message}`);
    }
  }, [isSupported, isListening]);

  // Stop listening
  const stopListening = useCallback(() => {
    if (!recognitionRef.current || !isListening) {
      return;
    }

    try {
      recognitionRef.current.stop();
    } catch (err) {
      console.error('Error stopping recognition:', err);
    }
  }, [isListening]);

  // Toggle listening
  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  }, [isListening, startListening, stopListening]);

  // Reset transcript
  const resetTranscript = useCallback(() => {
    setTranscript('');
    setInterimTranscript('');
    finalTranscriptRef.current = '';
  }, []);

  // Get combined transcript (final + interim)
  const getFullTranscript = useCallback(() => {
    return transcript + (interimTranscript ? ' ' + interimTranscript : '');
  }, [transcript, interimTranscript]);

  return {
    isListening,
    transcript,
    interimTranscript,
    error,
    isSupported,
    startListening,
    stopListening,
    toggleListening,
    resetTranscript,
    getFullTranscript,
  };
};

export default useSpeechRecognition;