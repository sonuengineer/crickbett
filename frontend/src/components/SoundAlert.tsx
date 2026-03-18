import { useEffect } from 'react';
import { useSound } from '../hooks/useSound';

export default function SoundAlert() {
  const { requestNotificationPermission } = useSound();

  useEffect(() => {
    requestNotificationPermission();
  }, []);

  // This is a utility component — renders nothing
  return null;
}
