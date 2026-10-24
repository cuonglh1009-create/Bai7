# Họ tên: Lê Hùng Cường
# MSSV:202418859

from abc import ABC, abstractmethod
from enum import Enum
from typing import TypeVar, Generic, List, Optional, Callable, Protocol, Set



#  ENUM & NGOẠI LỆ
class DeviceStatus(Enum):
    AVAILABLE = "Available"
    BORROWED = "Borrowed"
    UNDER_MAINTENANCE = "UnderMaintenance"


class DuplicateIdException(Exception):
    def __init__(self, duplicate_id: str):
        self.duplicate_id = duplicate_id
        super().__init__(f"Trùng mã thiết bị: {duplicate_id}")


class NoSuitableItemException(Exception):
    def __init__(self, message: str = "Không có thiết bị phù hợp để cấp phát"):
        super().__init__(message)


class DeviceNotReadyException(Exception):
    def __init__(self, device_id: str, current_status: DeviceStatus):
        self.device_id = device_id
        self.current_status = current_status
        super().__init__(f"Thiết bị {device_id} không sẵn sàng (trạng thái: {current_status.value})")


#   NHẬN DIỆN
class IIdentifiable(Protocol):
    @property
    def id(self) -> str: ...


#  LỚP TRỪU TƯỢNG
class TeachingDevice(ABC):
    def __init__(self, device_id: str, name: str, storage_location: str):
        if not device_id or not device_id.strip():
            raise ValueError("Id không được rỗng")
        if not name or not name.strip():
            raise ValueError("Name không được rỗng")
        if not storage_location or not storage_location.strip():
            raise ValueError("StorageLocation không được rỗng")

        self._id = device_id
        self._name = name
        self._storage_location = storage_location
        self._status = DeviceStatus.AVAILABLE

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def storage_location(self) -> str:
        return self._storage_location

    @property
    def status(self) -> DeviceStatus:
        return self._status

    @abstractmethod
    def is_ready_for_use(self) -> bool:
        """Kiểm tra khả năng sẵn sàng – đa hình theo loại thiết bị"""
        pass

    @abstractmethod
    def get_default_priority_score(self) -> float:
        """Điểm ưu tiên mặc định – đa hình theo loại thiết bị"""
        pass

    def borrow(self):
        if not self.is_ready_for_use():
            raise DeviceNotReadyException(self.id, self.status)
        self._status = DeviceStatus.BORROWED

    def return_device(self):
        if self._status != DeviceStatus.BORROWED:
            raise ValueError(f"Thiết bị {self.id} không ở trạng thái đang mượn")
        self._status = DeviceStatus.AVAILABLE

    def __str__(self) -> str:
        return (f"[{self.id}] {self.name} | Vị trí: {self.storage_location} | "
                f"TT: {self.status.value} | Ưu tiên: {self.get_default_priority_score():.1f}")


#  CÁC LỚP DẪN XUẤT
class ProjectorRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str, battery_level: int):
        super().__init__(device_id, name, storage_location)
        if not 0 <= battery_level <= 100:
            raise ValueError("BatteryLevel phải từ 0 đến 100")
        self._battery_level = battery_level

    @property
    def battery_level(self) -> int:
        return self._battery_level

    def is_ready_for_use(self) -> bool:
        return (self.status == DeviceStatus.AVAILABLE and
                self.battery_level >= 10)

    def get_default_priority_score(self) -> float:
        return float(self.battery_level)


class AirConditionerRemote(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str,
                 compatible_rooms: Set[str]):
        super().__init__(device_id, name, storage_location)
        self._compatible_rooms = set(compatible_rooms)

    @property
    def compatible_rooms(self) -> Set[str]:
        return set(self._compatible_rooms)

    def is_compatible_with(self, room_id: str) -> bool:
        return room_id in self._compatible_rooms

    def is_ready_for_use(self) -> bool:
        return self.status == DeviceStatus.AVAILABLE

    def get_default_priority_score(self) -> float:
        return 100.0 if self._compatible_rooms else 0.0


class WirelessMicrophone(TeachingDevice):
    def __init__(self, device_id: str, name: str, storage_location: str,
                 battery_level: int, signal_quality: int):
        super().__init__(device_id, name, storage_location)
        if not 0 <= battery_level <= 100:
            raise ValueError("BatteryLevel phải từ 0 đến 100")
        if not 0 <= signal_quality <= 100:
            raise ValueError("SignalQuality phải từ 0 đến 100")
        self._battery_level = battery_level
        self._signal_quality = signal_quality

    @property
    def battery_level(self) -> int:
        return self._battery_level

    @property
    def signal_quality(self) -> int:
        return self._signal_quality

    def is_ready_for_use(self) -> bool:
        return (self.status == DeviceStatus.AVAILABLE and
                self.battery_level >= 30 and
                self.signal_quality >= 40)

    def get_default_priority_score(self) -> float:
        return float(self.battery_level + self.signal_quality)


# GENERIC REPOSITOR
T = TypeVar("T", bound=IIdentifiable)


class IRepository(Generic[T], ABC):
    @abstractmethod
    def add(self, item: T) -> None: ...
    @abstractmethod
    def remove(self, item_id: str) -> bool: ...
    @abstractmethod
    def find_by_id(self, item_id: str) -> Optional[T]: ...
    @abstractmethod
    def get_all(self) -> List[T]: ...
    @abstractmethod
    def find_all(self, condition: Callable[[T], bool]) -> List[T]: ...


class InMemoryRepository(IRepository[T]):
    def __init__(self):
        self._items: dict[str, T] = {}

    def add(self, item: T) -> None:
        if item is None:
            raise ValueError("Không chấp nhận phần tử null")
        if item.id in self._items:
            raise DuplicateIdException(item.id)
        self._items[item.id] = item

    def remove(self, item_id: str) -> bool:
        if item_id in self._items:
            del self._items[item_id]
            return True
        return False

    def find_by_id(self, item_id: str) -> Optional[T]:
        return self._items.get(item_id)

    def get_all(self) -> List[T]:
        return list(self._items.values())

    def find_all(self, condition: Callable[[T], bool]) -> List[T]:
        return [item for item in self._items.values() if condition(item)]


# LỰA CHỌN
class ISelectionStrategy(Generic[T], ABC):
    @abstractmethod
    def select(self, candidates: List[T]) -> T: ...


class HighestPriorityStrategy(ISelectionStrategy[T]):
    def __init__(self, score_selector: Callable[[T], float]):
        self._score_selector = score_selector

    def select(self, candidates: List[T]) -> T:
        if not candidates:
            raise NoSuitableItemException()
        return max(candidates, key=self._score_selector)


class FirstAvailableStrategy(ISelectionStrategy[T]):
    def select(self, candidates: List[T]) -> T:
        if not candidates:
            raise NoSuitableItemException()
        return candidates[0]


# DỊCH VỤ CẤP PHÁT
class AllocationService(Generic[T]):
    def __init__(self, repository: IRepository[T], strategy: ISelectionStrategy[T]):
        self._repository = repository
        self._strategy = strategy

    def change_strategy(self, new_strategy: ISelectionStrategy[T]) -> None:
        self._strategy = new_strategy

    def allocate(self, additional_condition: Optional[Callable[[T], bool]] = None) -> T:
        """
        1. Lấy tất cả từ repository
        2. Lọc IsReadyForUse
        3. Áp dụng additional_condition
        4. Dùng strategy chọn
        5. Gọi borrow()
        6. Trả về thiết bị
        """
        candidates = self._repository.find_all(lambda d: d.is_ready_for_use())
        if additional_condition is not None:
            candidates = [c for c in candidates if additional_condition(c)]

        selected = self._strategy.select(candidates)
        selected.borrow()
        return selected


# = MENU & DEMO
def print_menu():
    print("\n HỆ THỐNG CẤP PHÁT THIẾT BỊ")
    print("1. Xem tất cả thiết bị trong kho")
    print("2. Lọc thiết bị sẵn sàng")
    print("3. Cấp phát Projector (ưu tiên pin cao nhất)")
    print("4. Cấp phát AirConditioner (tương thích phòng)")
    print("5. Cấp phát Microphone (chiến lược FirstAvailable)")
    print("6. Đổi chiến lược Projector sang FirstAvailable")
    print("7. Trả thiết bị theo mã")
    print("0. Thoát")



def main():
    # Khởi tạo repository generic cho từng loại
    projector_repo: InMemoryRepository[ProjectorRemote] = InMemoryRepository()
    ac_repo: InMemoryRepository[AirConditionerRemote] = InMemoryRepository()
    mic_repo: InMemoryRepository[WirelessMicrophone] = InMemoryRepository()

    # 3 Projector với pin khác nhau
    projector_repo.add(ProjectorRemote("PRJ01", "Điều khiển Epson", "Kệ A1", 85))
    projector_repo.add(ProjectorRemote("PRJ02", "Điều khiển BenQ", "Kệ A2", 45))
    projector_repo.add(ProjectorRemote("PRJ03", "Điều khiển Sony", "Kệ A1", 95))

    # 2 AirConditioner với phòng tương thích khác nhau
    ac_repo.add(AirConditionerRemote("AC01", "ĐK Điều hòa Daikin", "Kệ B1", {"A101", "A102", "A203"}))
    ac_repo.add(AirConditionerRemote("AC02", "ĐK Điều hòa LG", "Kệ B2", {"B201", "B202"}))

    # 3 Microphone
    mic_repo.add(WirelessMicrophone("MIC01", "Micro Shure", "Kệ C1", 70, 80))
    mic_repo.add(WirelessMicrophone("MIC02", "Micro Sennheiser", "Kệ C2", 25, 90))  # pin thấp → không ready
    mic_repo.add(WirelessMicrophone("MIC03", "Micro Sony", "Kệ C1", 60, 55))

    # Chiến lược & dịch vụ
    proj_strategy = HighestPriorityStrategy[ProjectorRemote](lambda d: d.get_default_priority_score())
    proj_service = AllocationService(projector_repo, proj_strategy)

    ac_strategy = HighestPriorityStrategy[AirConditionerRemote](lambda d: d.get_default_priority_score())
    ac_service = AllocationService(ac_repo, ac_strategy)

    mic_strategy = FirstAvailableStrategy[WirelessMicrophone]()
    mic_service = AllocationService(mic_repo, mic_strategy)

    print(" Dữ liệu mẫu đã sẵn sàng ")
    print(f"Projector: {len(projector_repo.get_all())} | AC: {len(ac_repo.get_all())} | Mic: {len(mic_repo.get_all())}")

    while True:
        print_menu()
        choice = input("Chọn chức năng: ").strip()

        try:
            if choice == "1":
                print("\n PROJECTOR ")
                for d in projector_repo.get_all():
                    print(" ", d)
                print(" AIR CONDITIONER ")
                for d in ac_repo.get_all():
                    print(" ", d)
                print(" MICROPHONE")
                for d in mic_repo.get_all():
                    print(" ", d)

            elif choice == "2":
                print("\nThiết bị sẵn sàng:")
                for d in projector_repo.find_all(lambda x: x.is_ready_for_use()):
                    print("  [PRJ]", d)
                for d in ac_repo.find_all(lambda x: x.is_ready_for_use()):
                    print("  [AC ]", d)
                for d in mic_repo.find_all(lambda x: x.is_ready_for_use()):
                    print("  [MIC]", d)

            elif choice == "3":
                selected = proj_service.allocate()
                print(f"Đã cấp phát: {selected}")
                print(f"  → Trạng thái sau cấp phát: {selected.status.value}")

            elif choice == "4":
                room = input("Nhập mã phòng cần tương thích (vd A203): ").strip() or "A203"
                selected = ac_service.allocate(lambda d: d.is_compatible_with(room))
                print(f"Đã cấp phát cho phòng {room}: {selected}")

            elif choice == "5":
                selected = mic_service.allocate()
                print(f"Đã cấp phát: {selected}")

            elif choice == "6":
                proj_service.change_strategy(FirstAvailableStrategy[ProjectorRemote]())
                print("Đã đổi chiến lược Projector sang FirstAvailableStrategy")
                selected = proj_service.allocate()
                print(f"Kết quả sau khi đổi: {selected}")

            elif choice == "7":
                did = input("Mã thiết bị cần trả: ").strip()
                device = None
                for repo in (projector_repo, ac_repo, mic_repo):
                    device = repo.find_by_id(did)
                    if device is not None:
                        break
                if device is None:
                    print("Không tìm thấy thiết bị.")
                else:
                    device.return_device()
                    print(f"Đã trả: {device}")

            elif choice == "0":
                print("Tạm biệt!")
                break
            else:
                print("Lựa chọn không hợp lệ.")

        except (NoSuitableItemException, DeviceNotReadyException, DuplicateIdException) as e:
            print(f"[LỖI NGHIỆP VỤ] {e}")
        except ValueError as e:
            print(f"[LỖI DỮ LIỆU] {e}")
        except Exception as e:
            print(f"[LỖI HỆ THỐNG] {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
