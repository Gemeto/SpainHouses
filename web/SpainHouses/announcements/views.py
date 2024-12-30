from django.views import generic
from django.db.models import Q
from announcements.models import Announcement
from sklearn.preprocessing import normalize
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pathlib import Path
from typing import Dict
import os
import sys
sys.path.append("../..")
from configuration import projectSettings

class MultiNumpyMMAPHandler:
    _instance = None
    _arrays: Dict[str, dict] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MultiNumpyMMAPHandler, cls).__new__(cls)
        return cls._instance

    def load_array(self, file_path):
        try:
            self._arrays[file_path] = np.load(Path(file_path), mmap_mode='r')
            return self._arrays[file_path]
        except Exception as e:
            raise Exception(f"Error al cargar el archivo numpy {file_path}: {str(e)}")
        
    def set_array(self, identifier, array):
        self._arrays[identifier] = array

    def get_array(self, file_path):
        if file_path not in self._arrays:
            return self.load_array(file_path)
        
        return self._arrays[file_path]
    
    def exist_array(self, file_path):
        return file_path in self._arrays

    def get_slice(self, file_path, indices):
        array = self.get_array(file_path)
        if array is None:
            return None
        return array[indices]

    def remove_array(self, file_path):
        if file_path in self._arrays:
            del self._arrays[file_path]
            return True
        return False

    def clear_all(self) -> None:
        for file_path in list(self._arrays.keys()):
            self.remove_array(file_path)

class AnnouncementListView(generic.ListView):
    model = Announcement
    paginate_by = 30
    context_object_name = 'offers_list'
    model_ids = Announcement.objects.order_by('ref', 'timestamp').distinct('ref').values('announcementid')
    queryset = Announcement.objects.filter(announcementid__in=model_ids).order_by('price')
    template_name = 'announcement/announcements_list.html'

    def get_queryset(self):
        queryset = super().get_queryset()
        
        queryset = queryset.filter(offer_type=self.request.GET.get('offerType', 1))
        queryset = queryset.filter(price__gte = self.request.GET.get('minPrice', 0))

        max_price = self.request.GET.get('maxPrice', None)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        queryset = queryset.filter(constructed_m2__gte=self.request.GET.get('minArea', 0))

        max_area = self.request.GET.get('maxArea', None)
        if max_area:
            queryset = queryset.filter(constructed_m2__lte=max_area)

        queryset = queryset.filter(rooms__gte=self.request.GET.get('minRooms', 0))

        publish_date = self.request.GET.get('publishDate', None)
        if publish_date:
            queryset = queryset.filter(update_date__gte=publish_date)

        queryset = queryset.filter(
            Q(title__contains=self.request.GET.get('fullTextSearch', '')) |
            Q(description__contains=self.request.GET.get('fullTextSearch', ''))
        )

        energy_calification = self.request.GET.get('energy_calification', None)
        if energy_calification:
            queryset = queryset.filter(energy_calification=energy_calification)

        construction_date = self.request.GET.get('constructionDate', None)
        if construction_date:
            queryset = queryset.filter(construction_date__gte=construction_date)
            
        platform = self.request.GET.get('platform', 0)
        if platform:
            queryset = queryset.filter(spider=platform)
        #queryset = queryset.filter(location__contains=self.request.GET.get('location', 0))
        #queryset = queryset.filter(rooms__gte=self.request.GET.get('energy_consumption', 0))

        for announcement in queryset:
            if os.path.exists(f"{projectSettings.IMAGES_PATH}/{announcement.ref}"):
                image_urls = os.listdir(f"{projectSettings.IMAGES_PATH}/{announcement.ref}")
                announcement.image_urls = image_urls[0]
            else:
                announcement.image_urls = None
            
        return queryset

class AnnouncementDetailView(generic.DetailView):
    model = Announcement
    template_name = 'announcement/announcement_detail.html'
    image_features_path = f'{projectSettings.IMAGE_FEATURES_PATH}/features.npy'
    image_ids_path = f'{projectSettings.IMAGE_FEATURES_PATH}/ids.npy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        #Processing similar offers only if image features file exist
        if os.path.exists(self.image_features_path) and os.path.exists(self.image_ids_path):
            #Getting the image features and ids into/from memory
            mem_array_handler = MultiNumpyMMAPHandler()

            if mem_array_handler.exist_array(self.image_features_path):
                features = mem_array_handler.get_array(self.image_features_path)
            else:
                features = mem_array_handler.get_array(self.image_features_path)
                mem_array_handler.set_array(self.image_features_path, normalize(features))

            ids = mem_array_handler.get_array(self.image_ids_path)

            #Finding similar offer ids
            similars = self.find_similar_images(self.object.ref, features, ids)

            #Getting similar offers from DB and adding them to the context
            similars = Announcement.objects.filter(ref__in=similars).order_by('ref').distinct('ref')
            context["similar_offers"] = similars

        #Adding announcement image paths to the context
        if os.path.exists(f"{projectSettings.IMAGES_PATH}/{self.object.ref}"):
            context["announcement_images"] = os.listdir(f"{projectSettings.IMAGES_PATH}/{self.object.ref}")

        #Adding announcement historic data to the context
        context["announcements"] = Announcement.objects.filter(ref=self.object.ref).order_by("timestamp")

        for offer in context.get("similar_offers", []):
            image_urls = os.listdir(f"{projectSettings.IMAGES_PATH}/{offer.ref}")
            if len(image_urls) > 0:
                offer.image_urls = image_urls[0]
            else:
                offer.image_urls = None
        return context
    
    def find_similar_images(self, selected_id, features, ids, top_n=3):
            unique_similar_ids = {}
            similarities = None
            similar_indices = None
            image_features_index = np.where(ids == selected_id)[0]

            if len(image_features_index) > 0:
                #Solo usamos la primera mitad del array porque se repiten
                for features_index in np.array_split(image_features_index, 2)[0]:
                    image_features = features[features_index]

                    #Calculate cosine similarity
                    similarities = cosine_similarity(image_features.reshape(1, -1), features)

                    #Sort matches by similarity in desc order
                    similar_indices = similarities[0].argsort()[::-1]

                    for idx in similar_indices:
                        similar_id = ids[idx]

                        #Setting simiar ids dict
                        if similar_id != selected_id and similar_id not in unique_similar_ids:
                            if float(similarities[0][idx]) < 0.77:
                                break
                            unique_similar_ids[similar_id] = similarities[0][idx]
                        if len(unique_similar_ids) >= top_n:
                            break

                    if len(unique_similar_ids) >= top_n:
                        break
            
            return list(unique_similar_ids.keys())
