package xiaozhi.modules.device.entity;

import java.util.Date;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;

import lombok.Data;

@Data
@TableName("ai_device_live_command_record")
public class LiveCommandRecordEntity {
    @TableId(type = IdType.AUTO)
    private Long id;

    @TableField("source")
    private String source;

    @TableField("record_id")
    private String recordId;

    @TableField("room_id")
    private String roomId;

    @TableField("room_title")
    private String roomTitle;

    @TableField("command_type")
    private String commandType;

    @TableField("priority_track")
    private String priorityTrack;

    @TableField("status")
    private String status;

    @TableField("target_device")
    private String targetDevice;

    @TableField("error_message")
    private String errorMessage;

    @TableField("payload")
    private String payload;

    @TableField("command_created_at")
    private Date commandCreatedAt;

    @TableField("dispatched_at")
    private Date dispatchedAt;

    @TableField("reported_at")
    private Date reportedAt;

    @TableField("updated_at")
    private Date updatedAt;
}