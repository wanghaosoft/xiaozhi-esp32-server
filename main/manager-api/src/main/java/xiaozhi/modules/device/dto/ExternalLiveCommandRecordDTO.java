package xiaozhi.modules.device.dto;

import java.util.Map;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ExternalLiveCommandRecordDTO {
    private String source;

    @NotBlank(message = "recordId 不能为空")
    private String recordId;

    private String roomId;
    private String roomTitle;

    @NotBlank(message = "commandType 不能为空")
    private String commandType;

    private String priorityTrack;
    private String status;
    private String targetDevice;
    private String errorMessage;
    private Map<String, Object> payload;
    private String commandCreatedAt;
    private String dispatchedAt;
}