import React, { useState, useEffect } from 'react';
import { api } from '../../core/api/client';
import { DataTable } from '../../shared/components/DataTable';
import { StatusBadge } from '../../shared/components/StatusBadge';
import { Boxes, Plus, ShoppingCart, RefreshCw, AlertCircle } from 'lucide-react';

export const InventoryView: React.FC = () => {
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [procureModalOpen, setProcureModalOpen] = useState(false);
  const [selectedItem, setSelectedItem] = useState<any | null>(null);
  const [procureQty, setProcureQty] = useState(5);
  const [procureJustification, setProcureJustification] = useState('Stock replenishment to prevent operational blocks');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const data = await api.getInventory();
      setItems(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProcurement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedItem) return;

    try {
      await api.createProcurement({
        item_id: selectedItem.id,
        quantity: procureQty,
        justification: procureJustification
      });
      setProcureModalOpen(false);
      alert('Procurement request generated and dispatched to Approvals Desk!');
      await loadData();
    } catch (err: any) {
      alert(`Procurement failed: ${err.message}`);
    }
  };

  const cols = [
    {
      header: 'Item Code',
      accessor: 'item_code' as const,
      render: (r: any) => <span className="font-mono font-bold text-[#345873]">{r.item_code}</span>
    },
    {
      header: 'Component Name',
      accessor: 'name' as const,
      render: (r: any) => <span className="font-bold text-gray-800 text-xs">{r.name}</span>
    },
    {
      header: 'Category',
      accessor: 'category' as const,
      render: (r: any) => <span className="capitalize text-gray-600">{r.category}</span>
    },
    {
      header: 'In Stock',
      accessor: 'stock_quantity' as const,
      render: (r: any) => (
        <span className={`font-mono font-bold ${r.stock_quantity <= r.minimum_threshold ? 'text-rose-600' : 'text-gray-800'}`}>
          {r.stock_quantity}
        </span>
      )
    },
    {
      header: 'Reserved',
      accessor: 'reserved_quantity' as const,
      render: (r: any) => <span className="font-mono text-gray-600">{r.reserved_quantity}</span>
    },
    {
      header: 'Available',
      render: (r: any) => {
        const avail = Math.max(0, r.stock_quantity - r.reserved_quantity);
        return (
          <span className={`font-mono font-bold px-2 py-0.5 rounded text-xs ${
            avail === 0 ? 'bg-rose-100 text-rose-800' : avail <= r.minimum_threshold ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
          }`}>
            {avail} units
          </span>
        );
      }
    },
    {
      header: 'Unit Cost',
      accessor: 'unit_cost' as const,
      render: (r: any) => <span className="font-mono">${Number(r.unit_cost || 0).toFixed(2)}</span>
    },
    {
      header: 'Action',
      render: (r: any) => (
        <button
          onClick={() => {
            setSelectedItem(r);
            setProcureModalOpen(true);
          }}
          className="px-2.5 py-1 bg-[#345873] text-white rounded-lg text-[11px] font-bold hover:bg-[#253f54] transition cursor-pointer"
        >
          Procure
        </button>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-[#345873]">Campus Inventory & Warehouse</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            35 catalogued spare parts, hardware components, and consumable supplies with transactional locks.
          </p>
        </div>

        <button
          onClick={loadData}
          className="p-2 bg-white text-gray-600 rounded-xl border border-slate-200 hover:bg-gray-50 cursor-pointer self-start sm:self-auto"
        >
          <RefreshCw size={16} />
        </button>
      </div>

      <DataTable
        columns={cols}
        data={items}
        keyField="id"
      />

      {/* Procurement Modal */}
      {procureModalOpen && selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-xs p-4">
          <div className="bg-white rounded-3xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <h3 className="text-base font-extrabold text-[#345873] mb-1">
              Procurement Request: {selectedItem.name}
            </h3>
            <p className="text-xs text-gray-500 mb-4">Item Code: {selectedItem.item_code}</p>

            <form onSubmit={handleCreateProcurement} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Requisition Quantity</label>
                <input
                  type="number"
                  min="1"
                  required
                  value={procureQty}
                  onChange={(e) => setProcureQty(parseInt(e.target.value) || 1)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
                <span className="text-[11px] text-gray-500 mt-1 block">
                  Total Estimated Cost: ${Number(procureQty * (selectedItem?.unit_cost || 0)).toFixed(2)}
                </span>
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Business Justification</label>
                <textarea
                  required
                  rows={3}
                  value={procureJustification}
                  onChange={(e) => setProcureJustification(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-slate-200 text-xs focus:ring-2 focus:ring-[#345873] focus:outline-none"
                />
              </div>

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setProcureModalOpen(false)}
                  className="px-4 py-2 text-xs font-bold text-gray-600 hover:text-gray-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#345873] text-white rounded-xl text-xs font-bold hover:bg-[#253f54] cursor-pointer"
                >
                  Submit for Approval
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

