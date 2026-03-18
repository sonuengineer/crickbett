import { useArbStore } from '../stores/arbStore';

export function useSound() {
  const { soundEnabled, toggleSound } = useArbStore();

  const requestNotificationPermission = async () => {
    if ('Notification' in window && Notification.permission === 'default') {
      await Notification.requestPermission();
    }
  };

  return { soundEnabled, toggleSound, requestNotificationPermission };
}
