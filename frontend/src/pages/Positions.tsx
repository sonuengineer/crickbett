import { useEffect, useState } from 'react';
import { getPositions, closePosition } from '../services/api';
import PositionTracker from '../components/PositionTracker';
import toast from 'react-hot-toast';

export default function Positions() {
  const [positions, setPositions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadPositions();
  }, []);

  const loadPositions = async () => {
    try {
      const res = await getPositions();
      setPositions(res.data);
    } catch {
      // handled
    } finally {
      setLoading(false);
    }
  };

  const handleClose = async (id: string) => {
    try {
      await closePosition(id);
      toast.success('Position closed');
      loadPositions();
    } catch {
      toast.error('Failed to close position');
    }
  };

  if (loading) {
    return <div className="text-center py-20 text-gray-500">Loading...</div>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-white mb-6">Hedge Positions</h1>
      <PositionTracker positions={positions} onClose={handleClose} />
    </div>
  );
}
