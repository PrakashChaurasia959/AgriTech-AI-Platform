import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  History as HistoryIcon, Search, Trash2, Download, FileText,
  ScanEye, Sprout, TrendingUp, ChevronLeft, ChevronRight, Eye,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { diseaseService } from '../services/disease.service';
import { cropService } from '../services/crop.service';
import { yieldService } from '../services/yield.service';
import { formatDate, downloadBlob } from '../utils';
import { usePageTitle } from '../hooks/usePageTitle';

type Tab = 'disease' | 'crop' | 'yield';

export default function History() {
  usePageTitle('My History');
  const [tab, setTab] = useState<Tab>('disease');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');

  const loadData = async () => {
    setLoading(true);
    try {
      let res;
      if (tab === 'disease') {
        res = await diseaseService.getHistory(page, 10, search);
      } else if (tab === 'crop') {
        res = await cropService.getHistory(page, 10);
      } else {
        res = await yieldService.getHistory(page, 10);
      }
      setData(res.items);
      setTotal(res.total);
      setTotalPages(Math.max(1, res.total_pages));
    } catch (err: any) {
      const msg = err?.response?.data?.detail || 'Failed to load history';
      toast.error(msg);
      setData([]);
      setTotal(0);
      setTotalPages(1);
    } finally {
      setLoading(false);
    }
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadData(); }, [tab, page]);

  // When search changes, reset to page 1 — the page change will trigger loadData above
  // If already on page 1, force a reload directly
  useEffect(() => {
    if (page === 1) {
      const timeout = setTimeout(() => { loadData(); }, 300);
      return () => clearTimeout(timeout);
    } else {
      const timeout = setTimeout(() => { setPage(1); }, 300);
      return () => clearTimeout(timeout);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search]);

  const handleDelete = async (id: string) => {
    try {
      if (tab === 'disease') await diseaseService.deleteHistory(id);
      else if (tab === 'crop') await cropService.deleteHistory(id);
      else await yieldService.deleteHistory(id);
      toast.success('Deleted successfully');
      loadData();
    } catch {
      toast.error('Delete failed');
    }
  };

  const handleDownload = async (id: string) => {
    try {
      let blob;
      if (tab === 'disease') blob = await diseaseService.downloadReport(id);
      else if (tab === 'crop') blob = await cropService.downloadReport(id);
      else blob = await yieldService.downloadReport(id);
      downloadBlob(blob, `${tab}_report_${id}.pdf`);
      toast.success('Report downloaded!');
    } catch {
      toast.error('Download failed');
    }
  };

  const tabs = [
    { key: 'disease' as Tab, label: 'Disease Scans', icon: ScanEye },
    { key: 'crop' as Tab, label: 'Crop Recommendations', icon: Sprout },
    { key: 'yield' as Tab, label: 'Yield Predictions', icon: TrendingUp },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <HistoryIcon className="w-7 h-7 text-primary-600" /> My History
        </h1>
        <p className="text-gray-500 mt-1">View and manage your past predictions and scans</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 overflow-x-auto">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => { setTab(t.key); setPage(1); }}
            className={`flex items-center gap-2 px-4 py-3 rounded-xl font-medium transition-all whitespace-nowrap ${
              tab === t.key
                ? 'bg-primary text-white shadow-md'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-50'
            }`}
          >
            <t.icon className="w-5 h-5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Search (only for disease) */}
      {tab === 'disease' && (
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-11"
            placeholder="Search by disease name..."
          />
        </div>
      )}

      {/* Table */}
      <div className="card overflow-hidden">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-4 border-primary-200 border-t-primary" />
          </div>
        ) : data.length === 0 ? (
          <div className="text-center py-12 text-gray-400">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>No records found. Start by using our AI tools!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  {tab === 'disease' && (
                    <>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Crop</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Disease</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Status</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Confidence</th>
                    </>
                  )}
                  {tab === 'crop' && (
                    <>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Top Crop</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">NPK</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">pH</th>
                    </>
                  )}
                  {tab === 'yield' && (
                    <>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Crop</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">State</th>
                      <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Yield (kg/ha)</th>
                    </>
                  )}
                  <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase">Date</th>
                  <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase">Actions</th>
                </tr>
              </thead>
              <tbody>
                {data.map((item) => (
                  <tr key={item.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    {tab === 'disease' && (
                      <>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{item.crop_type}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.disease_name}</td>
                        <td className="px-4 py-3">
                          <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                            item.is_healthy
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                          }`}>
                            {item.is_healthy ? 'Healthy' : 'Diseased'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{(item.confidence * 100).toFixed(1)}%</td>
                      </>
                    )}
                    {tab === 'crop' && (
                      <>
                        <td className="px-4 py-3 text-sm font-medium text-primary-600">{item.top_recommendation}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                          {item.nitrogen}/{item.phosphorus}/{item.potassium}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.ph}</td>
                      </>
                    )}
                    {tab === 'yield' && (
                      <>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-white">{item.crop_type}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{item.state}</td>
                        <td className="px-4 py-3 text-sm font-bold text-blue-600">{(item.predicted_yield ?? 0).toFixed(0)}</td>
                      </>
                    )}
                    <td className="px-4 py-3 text-sm text-gray-500">{formatDate(item.created_at)}</td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-end gap-2">
                        <button onClick={() => handleDownload(item.id)} className="p-2 rounded-lg hover:bg-blue-50 dark:hover:bg-blue-900/30 text-blue-500" title="Download report">
                          <Download className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(item.id)} className="p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/30 text-red-500" title="Delete">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t border-gray-100 dark:border-gray-800">
            <span className="text-sm text-gray-500">
              Page {page} of {totalPages} • {total} total records
            </span>
            <div className="flex gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-40"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
