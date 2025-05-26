import tracemalloc

from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse

class MemoryTest(APITestCase):
    def test_get_data_view(self):
        url = reverse('get_data')
        data = {
            'index-dropdown': 'SPY',
            'drawdown_range_min': '15',
            'drawdown_range_max': '30',
            'duration_range_min': '0',
            'duration_range_max': '1000',
            'recovery_target': '85'
        }
        tracemalloc.start()
        snapshot1 = tracemalloc.take_snapshot()
        response = self.client.post(url, data, format='json')
        snapshot2 = tracemalloc.take_snapshot()
        stats = snapshot2.compare_to(snapshot1, 'lineno')
        for stat in stats[:10]:
            print(stat)